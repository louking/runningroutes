###########################################################################################
# admin - administrative views for runningroutes database
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/05/17        Lou King        Create
#
#   Copyright 2017 Lou King.  All rights reserved
###########################################################################################

# standard
from itertools import zip_longest
from threading import RLock
from copy import deepcopy

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
from runningroutes import app
from runningroutes.models import db, Route, Role, Interest, ROLE_SUPER_ADMIN, ROLE_INTEREST_ADMIN
from loutilities.tables import CrudFiles, _uploadmethod, DbCrudApiRolePermissions
from loutilities.geo import LatLng, GeoDistance, elevation_gain, calculateBearing

APP_EARTH_RADIUS = app.config['APP_EARTH_RADIUS']
geodist = GeoDistance(APP_EARTH_RADIUS)

debug = False

idlocker = RLock()
# see https://developers.google.com/maps/documentation/elevation/usage-limits
# also used for google maps geocoding
gmapsclient = Client(key=app.config['GMAPS_ELEV_API_KEY'],queries_per_second=50)

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
########################################################################
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
#######################################################################
    # decorators = [auth_required(None)]

    def get(self):
        return render_template('admin.jinja2',
                               pagename='Admin Home')

admin_view = RunningRoutesAdmin.as_view('home')
bp.add_url_rule('/', view_func=admin_view, methods=['GET',])
bp.add_url_rule('/<interest>', view_func=admin_view, methods=['GET',])

#######################################################################
class RunningRoutesTable(DbCrudApiRolePermissions):
#######################################################################

    #----------------------------------------------------------------------
    def permission(self):
    #----------------------------------------------------------------------
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

        # if they're not logged in with ROLE_INTEREST_ADMIN role, they're bad
        interestadmin = Role.query.filter_by(name=ROLE_INTEREST_ADMIN).one()
        if not interestadmin in current_user.roles:
            return False

        # current_user has ROLE_INTEREST_ADMIN. Can this user access current interest?
        if self.interest in current_user.interests:
            return True
        else:
            return False
        
    #----------------------------------------------------------------------
    def createrow(self, formdata):
    #----------------------------------------------------------------------
        '''
        creates row in database
        
        :param formdata: data from create form
        :rtype: returned row for rendering, e.g., from DataTablesEditor.get_response_data()
        '''
        if debug: print('RunningRoutesTable.createrow()')

        # for location, snap to close loc, or create new one
        formdata['latlng'] = self.snaploc(formdata['location'])

        # make sure we record the row's interest
        formdata['interest_id'] = self.interest.id

        # and return the row
        return super(RunningRoutesTable, self).createrow(formdata)

    #----------------------------------------------------------------------
    def updaterow(self, thisid, formdata):
    #----------------------------------------------------------------------
        '''
        must be overridden

        updates row in database
        
        :param thisid: id of row to be updated
        :param formdata: data from create form
        :rtype: returned row for rendering, e.g., from DataTablesEditor.get_response_data()
        '''
        if debug: print('RunningRoutesTable.updaterow()')
        
        # for location, snap to close loc, or create new one
        formdata['latlng'] = self.snaploc(formdata['location'])
        
        return super(RunningRoutesTable, self).updaterow(formdata)

    #----------------------------------------------------------------------
    def snaploc(self, loc):
    #----------------------------------------------------------------------
        '''
        return "close" latlng for this loc

        :param loc: loc to look for
        :rtype: 'lat,lng' (6 decimal places)
        '''

        # convert loc to [lat, lng]
        ## if 'lat,lng', i.e., exactly two floating point numbers separated by comma
        try:
            checkloc = loc.split(',')
            if len(checkloc) != 2: raise ValueError
            latlng = [float(l) for l in checkloc]

        ## get lat, lng from google maps API
        except ValueError:
            app.logger.debug('snaploc() looking up loc = {}'.format(loc))
            # assume first location is best
            geoloc = gmapsclient.geocode(loc)[0]
            lat = float(geoloc['geometry']['location']['lat'])
            lng = float(geoloc['geometry']['location']['lng'])
            latlng = [lat, lng]

        # determine column which holds latlng data
        fid = self.app.config['RR_DB_SHEET_ID']
        hdrvalues = list(self.sheets.spreadsheets().values()).get(spreadsheetId=fid, range='routes!1:1').execute()['values']
        app.logger.debug('snaploc() header values = {}'.format(hdrvalues))
        header = hdrvalues[0]
        # there will be less than 26 columns
        latlngcol = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[header.index('latlng')]

        # retrieve lat,lng data already saved
        rows = list(self.sheets.spreadsheets().values()).get(spreadsheetId=fid, range='routes!{c}:{c}'.format(c=latlngcol)).execute()['values']
        # skip header row
        start_locs = [[float(v) for v in r[0].split(',')] for r in rows[1:]]

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
    #----------------------------------------------------------------------
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
        # configfile = self.app.config['APP_JS_CONFIG']
        # args['pagejsfiles'] += [ configfile ]

        return render_template( 'datatables.jinja2', **args )

#######################################################################
class RunningRoutesFiles(CrudFiles):
#######################################################################

    #----------------------------------------------------------------------
    def __init__(self, **kwargs):
    #----------------------------------------------------------------------
        if debug: print('RunningRoutesFiles.__init__() **kwargs={}'.format(kwargs))
        self.datafolderid = None
        super(RunningRoutesFiles, self).__init__(**kwargs)
        if debug: print('RunningRoutesFiles self.app = {}'.format(self.app))


    #----------------------------------------------------------------------
    def upload(self):
    #----------------------------------------------------------------------
        if (debug): print('RunningRoutesFiles.upload()')

        self._set_services()

        thisfile = request.files['upload']
        filename = thisfile.filename
        filetype = filename.split('.')[-1]

        filecontents = thisfile.readlines()
        thisfile.seek(0)
        latlng = LatLng(thisfile, filetype)
        locations = latlng.getpoints()

        thisss = self.sheets.spreadsheets().create(body={
                'properties' : { 'title' : filename },
                'sheets' : [
                    { 'properties' : { 'title' : filename } },
                    { 'properties' : { 'title' : 'path' } },
                    { 'properties' : { 'title' : 'turns' } },
                ]
            }).execute();
        
        # put file in appropriate folder
        # see https://stackoverflow.com/questions/42938990/google-sheets-api-create-or-move-spreadsheet-into-folder
        fileid = thisss['spreadsheetId']
        thisfile = self.drive.files().get( fileId=fileid, fields='parents' ).execute()
        parents = ','.join(thisfile['parents'])
        self.drive.files().update( fileId=fileid, removeParents=parents, addParents=self.datafolderid ).execute()

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
            gelevs += [[p['location']['lat'], p['location']['lng'], p['elevation'], p['resolution']] for p in elev]

        # calculate elevation gain
        elevations = numpy.array([float(p[2]) for p in gelevs])
        upthreshold = self.app.config['APP_ELEV_UPTHRESHOLD']
        downthreshold = self.app.config['APP_ELEV_DOWNTHRESHOLD']
        smoothwin = self.app.config['APP_SMOOTHING_WINDOW']

        ## first smooth the elevations using flat window
        ## see http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
        s = numpy.r_[elevations[smoothwin-1:0:-1],elevations,elevations[-2:-smoothwin-1:-1]]
        w = numpy.ones(smoothwin,'d')
        y=numpy.convolve(w/w.sum(),s,mode='valid')
        smoothed = y[(smoothwin/2):-(smoothwin/2)]
        # reference suggested below to 
        # smoothed = y[(smoothwin/2-1):-(smoothwin/2)]

        ## calculate the gain using the smoothed elevation profile
        gain = elevation_gain(smoothed, upthreshold=upthreshold, downthreshold=downthreshold)

        # combine gelevs with anno
        if len(gelevs) != len(anno) or len(gelevs) != len(smoothed):
            app.logger.debug('invalid list len len(gelevs)={} len(anno)={} len(smoothed)={}'.format(len(gelevs), len(anno), len(smoothed)))

        # construct rows we're going to save to the path sheet
        pathrows = []
        smoothedl = [[e] for e in smoothed]
        for i in range(len(gelevs)):
            try:
                pathrows.append(gelevs[i] + smoothedl[i] + anno[i])
            except IndexError:
                pathrows.append(gelevs[i])

        # update sheet with data values
        list(self.sheets.spreadsheets().values()).batchUpdate(spreadsheetId=fileid, body={
                'valueInputOption' : 'USER_ENTERED',
                'data' : [
                    { 'range' : filename, 'values' : [['content']] + [[r.rstrip()] for r in filecontents]},
                    { 'range' : 'path',   'values' : [['lat', 'lng', 'orig ele', 'res', 'ele', 'cumdist(km)', 'inserted']] + pathrows },
                ]
            }).execute()

        return {
            'upload' : {'id': fileid },
            'files' : {
                'data' : {
                    fileid : {'filename': filename}
                },
            },
            # round for user-friendly display
            'elev' : int(round(gain)),
            'distance': '{:.1f}'.format(distance),
            'filename': filename,
            # start defaults to first point
            'location' : ', '.join(['{:.6f}'.format(ll) for ll in locations[0]])
        }

    #----------------------------------------------------------------------
    def list(self):
    #----------------------------------------------------------------------
        if (debug): print('RunningRoutesFiles.list()')

        self._set_services()

        # list files whose parent is datafolderid
        table = 'data'
        filelist = {table:{}}
        # datafiles = self.drive.files().list(q="'{}' in parents".format(self.datafolderid)).execute()
        # while True:
        #     for thisfile in datafiles['files']:
        #         filelist[table][thisfile['id']] = {'filename' : thisfile['name']}
        #
        #     if 'nextPageToken' not in datafiles: break
        #     datafiles = self.drive.files().list(q="'{}' in parents".format(self.datafolderid), pageToken=datafiles['nextPageToken']).execute()

        return filelist


    #----------------------------------------------------------------------
    def _set_services(self):
    #----------------------------------------------------------------------
        if (debug): print('RunningRoutesFiles._set_services()')

        # if not self.datafolderid:
        #     credentials = get_credentials(APP_CRED_FOLDER)
        #     self.drive = discovery.build(DRIVE_SERVICE, DRIVE_VERSION, credentials=credentials)
        #     self.sheets = discovery.build(SHEETS_SERVICE, SHEETS_VERSION, credentials=credentials)
        #     fid = self.app.config['RR_DB_SHEET_ID']
        #     datafolder = list(self.sheets.spreadsheets().values()).get(spreadsheetId=fid, range='datafolder').execute()
        #     self.datafolderid = datafolder['values'][0][0]

#############################################
# google auth views
# appscopes = [ 'https://www.googleapis.com/auth/userinfo.email',
#               'https://www.googleapis.com/auth/userinfo.profile',
#               'https://www.googleapis.com/auth/spreadsheets',
#               'https://www.googleapis.com/auth/drive' ]
# googleauth = GoogleAuth(app, app.config['APP_CLIENT_SECRETS_FILE'], appscopes, 'admin',
#                         credfolder=APP_CRED_FOLDER,
#                         logincallback=do_login, logoutcallback=do_logout,
#                         loginfo=app.logger.info, logdebug=app.logger.debug, logerror=app.logger.error)


#############################################
# files handling
rrfiles = RunningRoutesFiles(
             app = bp,
             uploadendpoint = 'upload',
            )

#############################################
# admin views
def jsconfigfile():
    with app.app_context(): 
        return current_app.config['APP_JS_CONFIG']

admin_dbattrs = 'id,interest_id,name,distance,start_location,latlng,surface,elevation_gain,map,fileid,description,active'.split(',')
admin_formfields = 'rowid,interest_id,name,distance,location,latlng,surface,elev,map,fileid,description,active'.split(',')
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
                             # files = rrfiles,
                             eduploadoption = {
                                'type': 'POST',
                                'url':  'admin/upload',
                             },
                             dbmapping = admin_dbmapping,
                             formmapping = admin_formmapping,
                             buttons = ['create', 'edit'],
                             clientcolumns =  [
            { 'name': 'name',        'data': 'name',        'label': 'Route Name', 'fieldInfo': 'name you want to call this route' },
            { 'name': 'description', 'data': 'description', 'label': 'Description', 'fieldInfo' : 'optionally give details of where to meet here, e.g., name of the business' },
            { 'name': 'surface',     'data': 'surface',     'label': 'Surface',     'type': 'select',
                                                                            'options': ['road','trail','mixed']},
            { 'name': 'map',         'data': 'map',         'label': 'Route URL', 'fieldInfo': 'URL from mapmyrun, strava, etc., where route was created' },
            # { 'name': 'turns',      'data': 'fileid',      'label': 'Turns',
            #         'ed' : {'type': 'textarea',
            #                 'attr': {'placeholder': 'enter or paste turn by turn directions, carriage return between each turn'},
            #                },
            #         'dt' : {'visible': False},
            # },
            { 'name': 'fileid',      'data': 'fileid',      'label': 'File',
                    'ed' : {'type': 'upload',
                            'fieldInfo': 'use GPX file downloaded from mapmyrun, strava, etc.',
                            'dragDrop': False,
                            'display': 'rendergpxfile()'},
                    'dt' : {'render': 'rendergpxfile()'},
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
        ]);
rrtable.register()


#######################################################################
class RunningRoutesTurns(MethodView):
#######################################################################
    #----------------------------------------------------------------------
    def __init__(self, **kwargs):
    #----------------------------------------------------------------------
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
    #----------------------------------------------------------------------
        '''
        add endpoint to retrieve turns
        '''
        turns_view = self.as_view('turns')
        self.app.add_url_rule('/<fileid>/turns', view_func=turns_view, methods=['GET',])

    #----------------------------------------------------------------------
    @_uploadmethod()
    def get(self, fileid):
    #----------------------------------------------------------------------
        if debug: print('RunningRoutesTurns.get() self = {}, fileid = {}'.format(self, fileid))
        self._set_services()

        values = list(self.sheets.spreadsheets().values()).get(spreadsheetId=fileid, range='turns').execute()['values']
        # skip sheet header row
        turns = [r[0] for r in values[1:] if r]
        if debug: print('RunningRoutesTurns.get() turns={}'.format(turns))
        self._responsedata = {'turns': '\n'.join(turns)}

    #----------------------------------------------------------------------
    def _set_services(self):
    #----------------------------------------------------------------------
        if (debug): print('RunningRoutesFiles._set_services()')

        if not self.sheets:
            credentials = get_credentials(APP_CRED_FOLDER)
            self.sheets = discovery.build(SHEETS_SERVICE, SHEETS_VERSION, credentials=credentials)

#############################################
# turns handling
rrturns = RunningRoutesTurns(app=bp)
rrturns.register()

