###########################################################################################
# routes - administrative views for runningroutes database, routes management
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/05/17        Lou King        Create
#
#   Copyright 2017 Lou King.  All rights reserved
###########################################################################################

# standard
from copy import deepcopy
from csv import DictWriter

# pypi
from flask import g, render_template, redirect, request, url_for, current_app
from flask.views import MethodView
from flask_security import auth_required
from flask_security import current_user

# from apiclient import discovery # google api
# from apiclient.errors import HttpError
from googlemaps.client import Client
from googlemaps.elevation import elevation_along_path, elevation
import numpy

# homegrown
from . import bp
from runningroutes.files import create_fidfile
from runningroutes import app
from runningroutes.geo import GmapsLoc
from runningroutes.models import db, Route, Role, Interest, Files, ROLE_SUPER_ADMIN, ROLE_ROUTES_ADMIN
from loutilities.tables import CrudFiles, _uploadmethod, DbCrudApiRolePermissions
from loutilities.geo import LatLng, GeoDistance, elevation_gain, calculateBearing

APP_EARTH_RADIUS = app.config['APP_EARTH_RADIUS']
geodist = GeoDistance(APP_EARTH_RADIUS)

debug = False

# see https://developers.google.com/maps/documentation/elevation/usage-limits
# also used for google maps geocoding
gmapsclient = Client(key=app.config['GMAPS_ELEV_API_KEY'],queries_per_second=50)
gmaps = GmapsLoc(app.config['GMAPS_ELEV_API_KEY'])

# configuration
## note resolution is about 9.5 meters, so no need to have points
## closer than within that radius
FT_PER_SAMPLE = 60 # feet
MAX_SAMPLES = 512

# calculated
MI_PER_SAMPLE = FT_PER_SAMPLE / 5280.0
SAMPLES_PER_MILE = 5280 / FT_PER_SAMPLE # int
GELEV_MAX_MILES = MAX_SAMPLES*1.0 / SAMPLES_PER_MILE

class GoogleApiError(Exception): pass
class IdNotFound(Exception): pass

########################################################################
class rowObj(dict):
    '''
    subclass dict to make it work like an object

    see http://goodcode.io/articles/python-dict-object/
    '''
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

#######################################################################
class RunningRoutesAdmin(MethodView):
    decorators = [auth_required()]

    def get(self):
        return render_template('admin.jinja2',
                               pagename='Admin Home',
                               # causes redirect to current interest if bare url used
                               url_rule='/admin/<interest>',
                               )

admin_view = RunningRoutesAdmin.as_view('home')
bp.add_url_rule('/', view_func=admin_view, methods=['GET',])
bp.add_url_rule('/<interest>', view_func=admin_view, methods=['GET',])

#######################################################################
class RunningRoutesTable(DbCrudApiRolePermissions):

    decorators = [auth_required()]

    #----------------------------------------------------------------------
    def permission(self):
        '''
        check for permission on data
        :rtype: boolean
        '''
        if debug: print('RunningRoutesTable.permission()')

        # need to be logged in
        if not current_user.is_authenticated:
            return False

        # g.interest initialized in runningroutes.create_app.pull_interest
        # g.interest contains slug, pull in interest db entry. If not found, no permission granted
        self.interest = Interest.query.filter_by(interest=g.interest).one_or_none()
        if not self.interest:
            return False

        # is someone logged in with ROLE_SUPER_ADMIN role? They're good
        superadmin = Role.query.filter_by(name=ROLE_SUPER_ADMIN).one()
        if superadmin in current_user.roles:
            return True

        # if they're not logged in with ROLE_ROUTES_ADMIN role, they're bad
        routesadmin = Role.query.filter_by(name=ROLE_ROUTES_ADMIN).one()
        if not routesadmin in current_user.roles:
            return False

        # current_user has ROLE_ROUTES_ADMIN. Can this user access current interest?
        if self.interest in current_user.interests:
            return True
        else:
            return False
        
    #----------------------------------------------------------------------
    def beforequery(self):
        '''
        filter on current interest
        :return:
        '''
        interest = Interest.query.filter_by(interest=g.interest).one()
        self.queryparams['interest_id'] = interest.id

    #----------------------------------------------------------------------
    def set_files_route(self, route_id, fileidlist=[]):
        '''
        leaves files in fileidlist as pointing to specified route
        caller must flush / commit

        :param route_id: id of current route
        :param fileidlist: list of file ids to set to leaving pointing at current route,
            leave empty when deleting route
        :return: None
        '''
        # remove old files
        oldfiles = Files.query.filter_by(route_id=route_id).all()
        for file in oldfiles:
            file.route_id = None

        for fileid in fileidlist:
            file = Files.query.filter_by(fileid=fileid).one()
            file.route_id = route_id

    #----------------------------------------------------------------------
    def createrow(self, formdata):
        '''
        creates row in database
        
        :param formdata: data from create form
        :rtype: returned row for rendering, e.g., from DataTablesEditor.get_response_data()
        '''
        if debug: print('RunningRoutesTable.createrow()')

        # for location, snap to close loc, or create new one
        # this needs to be before updating the row start_location in the database
        formdata['latlng'] = self.snaploc(formdata['location'])

        # make sure we record the row's interest
        formdata['interest_id'] = self.interest.id

        # return the row
        route =  super(RunningRoutesTable, self).createrow(formdata)
        self.set_files_route(route['rowid'], [route['gpx_file_id'], route['path_file_id']])

        return route

    #----------------------------------------------------------------------
    def updaterow(self, thisid, formdata):
        '''
        updates row in database
        
        :param thisid: id of row to be updated
        :param formdata: data from create form
        :rtype: returned row for rendering, e.g., from DataTablesEditor.get_response_data()
        '''
        if debug: print('RunningRoutesTable.updaterow()')
        
        # for location, snap to close loc, or create new one
        formdata['latlng'] = self.snaploc(formdata['location'])
        
        route = super(RunningRoutesTable, self).updaterow(thisid, formdata)
        self.set_files_route(route['rowid'], [route['gpx_file_id'], route['path_file_id']])

        return route

    #----------------------------------------------------------------------
    def snaploc(self, loc):
        '''
        return "close" latlng for this loc

        :param loc: loc to look for
        :rtype: 'lat,lng' (6 decimal places)
        '''

        # convert loc to (lat, lng)
        latlng = gmaps.loc2latlng(loc)

        # retrieve lat,lng data already saved; self.queryparams filters by interest
        route_rows = Route.query.filter_by(**self.queryparams).all()
        start_locs = [[float(v) for v in r.latlng.split(',')] for r in route_rows]

        # check if start location is "close" to any existing location. If so, snap to existing location
        epsilon = app.config['APP_ROUTE_LOC_EPSILON']/1000.0   # convert to km
        this_loc = latlng
        for start_loc in start_locs:
            # haversineDistance returns km
            if geodist.haversineDistance(this_loc, start_loc, False) <= epsilon:
                this_loc = start_loc
                break

        # normalize format to 6 decimal places
        return ','.join(['{:.6f}'.format(l) for l in this_loc])

    #----------------------------------------------------------------------
    def render_template(self, **kwargs):
        '''
        renders flask template with appropriate parameters
        :param tabledata: list of data rows for rendering
        :rtype: flask.render_template()
        '''
        # the args dict has all the defined parameters to 
        # caller supplied keyword args are used to update the defaults
        # all arguments are made into attributes for self
        if debug: print('RunningRoutesTable.render_template()')

        args = deepcopy(kwargs)

        return render_template( 'datatables.jinja2', **args )

#######################################################################
class RunningRoutesFiles(CrudFiles):

    #----------------------------------------------------------------------
    def __init__(self, **kwargs):

        if debug: print('RunningRoutesFiles.__init__() **kwargs={}'.format(kwargs))
        self.datafolderid = None
        super(RunningRoutesFiles, self).__init__(**kwargs)
        if debug: print('RunningRoutesFiles self.app = {}'.format(self.app))


    #----------------------------------------------------------------------
    def upload(self):

        if (debug): print('RunningRoutesFiles.upload()')

        # save gpx file
        thisfile = request.files['upload']
        gpx_fid, filepath = create_fidfile(g.interest, thisfile.filename, thisfile.mimetype)
        thisfile.save(filepath)
        thisfile.seek(0)

        # process file data; update route with calculated values
        # open file
        # process file contents
        filename = thisfile.filename
        filetype = filename.split('.')[-1]

        # latlng processing depends on file type
        latlng = LatLng(thisfile, filetype)
        locations = latlng.getpoints()

        # calculate distance in km
        distance = 0.0
        maxinterval = app.config['APP_MAX_DIST_INTERVAL']/1000.0  # convert m to km
        locs = [locations[0]]
        # anno is list of [cumdist, inserted], where inserted is empty or 'inserted'
        anno = [[0, '']]
        for i in range(1,len(locations)):
            thisdist = geodist.haversineDistance(locations[i-1], locations[i], False)
            eachdist = thisdist
            # add additional points if the distance between these is longer than allowed
            if thisdist > maxinterval:
                numnew = int(thisdist / maxinterval)
                eachdist = thisdist / (numnew+1)
                bearing = calculateBearing(locations[i-1], locations[i])
                lastcoord = locations[i-1]
                for j in range(numnew):
                    distance += eachdist
                    anno.append([distance, 'inserted'])
                    # getDestinationLatLng expects distance in meters
                    newcoord = geodist.getDestinationLatLng(lastcoord, bearing, eachdist*1000)
                    locs.append(newcoord)
                    lastcoord = newcoord
            distance += eachdist
            anno.append([distance, ''])
            locs.append(locations[i])

        # convert to miles
        distance /= 1.609344

        # query for elevation points
        ## slice off locations which meet max sample requirements from google for each query
        pathlen = MAX_SAMPLES
        gelevs = []
        while len(locs) > 0:
            if debug: print('len(locs) = {}'.format(len(locs)))

            theselocs = locs[:pathlen]
            del locs[:pathlen]

            ## get this set of elevations
            elev = elevation(gmapsclient, theselocs)
            # keys need to match Path fields
            gelevs += [{'lat':p['location']['lat'], 'lng':p['location']['lng'], 'orig_ele':p['elevation'], 'res':p['resolution']} for p in elev]

        # calculate elevation gain
        elevations = numpy.array([float(p['orig_ele']) for p in gelevs])
        upthreshold = current_app.config['APP_ELEV_UPTHRESHOLD']
        downthreshold = current_app.config['APP_ELEV_DOWNTHRESHOLD']
        smoothwin = current_app.config['APP_SMOOTHING_WINDOW']

        ## first smooth the elevations using flat window
        ## see http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
        s = numpy.r_[elevations[smoothwin-1:0:-1],elevations,elevations[-2:-smoothwin-1:-1]]
        w = numpy.ones(smoothwin,'d')
        y=numpy.convolve(w/w.sum(),s,mode='valid')
        # use floor division operator // (new in python 3)
        smoothed = y[(smoothwin//2):-(smoothwin//2)]
        # smoothedl = [[e] for e in smoothed]
        # reference suggested below to
        # smoothed = y[(smoothwin/2-1):-(smoothwin/2)]

        ## calculate the gain using the smoothed elevation profile
        gain = elevation_gain(smoothed, upthreshold=upthreshold, downthreshold=downthreshold)

        # combine gelevs with anno
        if len(gelevs) != len(anno) or len(gelevs) != len(smoothed):
            app.logger.debug('invalid list len len(gelevs)={} len(anno)={} len(smoothed)={}'.format(len(gelevs), len(anno), len(smoothed)))

        # create csv file with calculated path points
        # create/write path file
        # see https://stackoverflow.com/questions/7076042/what-mime-type-should-i-use-for-csv
        # see https://tools.ietf.org/html/rfc7111
        path_fid, filepath = create_fidfile(g.interest, thisfile.filename+'.csv', 'text/csv')
        with open(filepath, mode='w', newline='') as csvfile:
            pathfields = 'lat,lng,orig_ele,res,ele,cumdist_km,inserted'.split(',')
            pathcsv = DictWriter(csvfile, fieldnames=pathfields)
            pathcsv.writeheader()

            for ndx in range(len(gelevs)):
                # TODO: this is probably a bit klunky from being ported from use of google sheets, clean up
                try:
                    ele = smoothed[ndx]
                except IndexError:
                    ele = None
                try:
                    cumdist_km = anno[ndx][0]
                    inserted = anno[ndx][1]
                except IndexError:
                    cumdist_km = None
                    inserted = None

                thispoint = dict(
                            ele = ele,
                            cumdist_km = cumdist_km,
                            inserted = inserted,
                            **gelevs[ndx],
                            )

                pathcsv.writerow(thispoint)


        return {
            'upload' : {'id': gpx_fid },
            'files' : {
                'data' : {
                    gpx_fid : {'filename': thisfile.filename}
                },
            },
            'gpx_file_id' : gpx_fid,
            'path_file_id' : path_fid,
            # add calculated stuff to route
            # round for user-friendly display
            'elevation_gain' : int(round(gain)),
            'distance' : '{:.1f}'.format(distance),
            'start_location' : ', '.join(['{:.6f}'.format(ll) for ll in locations[0]])
        }

    #----------------------------------------------------------------------
    def list(self):

        if (debug): print('RunningRoutesFiles.list()')

        # list files whose parent is datafolderid
        table = 'data'
        filelist = {table:{}}
        files = Files.query.all()
        for file in files:
            filelist[table][file.fileid] = {'filename': file.filename}

        return filelist

#############################################
# files handling
rrfiles = RunningRoutesFiles(
    app = bp,
    uploadendpoint = 'upload',
    uploadrule='/<interest>/upload',
)

#############################################
# admin views
def jsconfigfile():
    with app.app_context(): 
        return current_app.config['APP_JS_CONFIG']

admin_dbattrs = 'id,interest_id,name,distance,start_location,latlng,surface,elevation_gain,map,turns,gpx_file_id,path_file_id,description,active'.split(',')
admin_formfields = 'rowid,interest_id,name,distance,location,latlng,surface,elev,map,turns,gpx_file_id,path_file_id,description,active'.split(',')
admin_dbmapping = dict(list(zip(admin_dbattrs, admin_formfields)))
admin_formmapping = dict(list(zip(admin_formfields, admin_dbattrs)))
rrtable = RunningRoutesTable(app=bp,
                             db = db,
                             pagename = 'Edit Routes',
                             model = Route,
                             idSrc = 'rowid',
                             rule = '/<interest>/routetable',
                             endpoint = 'admin.routetable',
                             endpointvalues = {'interest':'<interest>'},
                             files = rrfiles,
                             eduploadoption = {
                                'type': 'POST',
                                'url':  '/admin/<interest>/upload',
                             },
                             dbmapping = admin_dbmapping,
                             formmapping = admin_formmapping,
                             buttons = ['create', 'edit'],
                             clientcolumns =  [
            { 'name': 'name',        'data': 'name',        'label': 'Route Name', 'fieldInfo': 'name you want to call this route',
              'className': 'field_req'
              },
            { 'name': 'description', 'data': 'description', 'label': 'Description', 'fieldInfo' : 'optionally give details of where to meet here, e.g., name of the business' },
            { 'name': 'surface',     'data': 'surface',     'label': 'Surface',     'type': 'select2',
              'options': ['road','trail','mixed'],
              'ed' : {'def' : 'road'}
              },
            { 'name': 'map',         'data': 'map',         'label': 'Route URL', 'fieldInfo': 'URL from mapmyrun, strava, etc., where route was created' },
            { 'name': 'turns',      'data': 'turns',      'label': 'Turns',
                    'ed' : {'type': 'textarea',
                            'attr': {'placeholder': 'enter or paste turn by turn directions, carriage return between each turn'},
                           },
                    'dt' : {'visible': False},
            },
            { 'name': 'gpx_file_id',      'data': 'gpx_file_id',      'label': 'Gpx File',
              'className': 'field_req',
              'ed' : {'type': 'upload',
                            'fieldInfo': 'use GPX file downloaded from mapmyrun, strava, etc.',
                            'dragDrop': False,
                            'display': 'renderfileid()'},
                    'dt' : {'render': 'renderfileid()'},
              },
            { 'name': 'path_file_id',      'data': 'path_file_id',      'label': 'Path File',
              'ed': {'className': 'Hidden'},
              'dt': {'visible': False},
              },
            { 'name': 'location',    'data': 'location',    'label': 'Start Location', 'fieldInfo' : 'start location from GPX file - you may override, e.g., with address. Please make sure this value is valid search location in Google maps'},
            { 'name': 'latlng',      'data': 'latlng',      'label': 'Loc lat,lng',       
                    'ed' : {'className': 'Hidden'},
                    'dt' : {'visible': False},
            },
            { 'name': 'distance',    'data': 'distance',    'label': 'Distance (miles)', 'fieldInfo': 'calculated from GPX file - you may override'},
            { 'name': 'elev',        'data': 'elev',        'label': 'Elev Gain (ft)', 'fieldInfo': 'calculated from GPX file - you may override'},
            { 'name': 'active',      'data': 'active',      'label': 'Active',         'fieldInfo': 'when set to "deleted" will not show to users',
                    'ed' : {'type':'select', 'options':{'active':1, 'deleted':0}},
                    'dt' : {'render': 'renderactive()'},
            },
        ])
rrtable.register()


#######################################################################
class RunningRoutesTurns(MethodView):

    #----------------------------------------------------------------------
    def __init__(self, **kwargs):

        # the args dict has all the defined parameters to
        # caller supplied keyword args are used to update the defaults
        # all arguments are made into attributes for self
        if debug: print('RunningRoutesTurns.__init__() **kwargs={}'.format(kwargs))

        self.kwargs = kwargs
        args = dict(app = None,
                    )
        args.update(kwargs)        
        for key in args:
            setattr(self, key, args[key])

        self.sheets = None

    #----------------------------------------------------------------------
    def register(self):
        '''
        add endpoint to retrieve turns
        '''
        turns_view = self.as_view('turns')
        self.app.add_url_rule('/<fileid>/turns', view_func=turns_view, methods=['GET',])

    #----------------------------------------------------------------------
    @_uploadmethod()
    def get(self, fileid):

        if debug: print('RunningRoutesTurns.get() self = {}, fileid = {}'.format(self, fileid))
        self._set_services()

        values = list(self.sheets.spreadsheets().values()).get(spreadsheetId=fileid, range='turns').execute()['values']
        # skip sheet header row
        turns = [r[0] for r in values[1:] if r]
        if debug: print('RunningRoutesTurns.get() turns={}'.format(turns))
        self._responsedata = {'turns': '\n'.join(turns)}

#############################################
# turns handling
rrturns = RunningRoutesTurns(app=bp)
rrturns.register()

