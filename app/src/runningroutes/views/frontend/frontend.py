###########################################################################################
# frontend - views for runningroutes database
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/05/19        Lou King        Create
#
#   Copyright 2019 Lou King.  All rights reserved
###########################################################################################
'''
frontend - views for runningroutes database
=======================================================================
'''
# standard
from csv import DictReader
from urllib.parse import quote
from os.path import join

# pypi
from flask import g, redirect, url_for, abort, render_template, jsonify, request, send_file, current_app
from flask_security import current_user
from loutilities.user.model import Interest, Role

from runningroutes.helpers import local2common_interest, localinterest

# home grown
from . import bp
from runningroutes import app
from flask.views import MethodView
from runningroutes.models import LocalInterest, db, Route, Files, IconMap, ROLE_SUPER_ADMIN, ROLE_ROUTES_ADMIN
from runningroutes.files import get_fidfile
from ...helpers import local2common_interest

debug = False

#######################################################################
class Index(MethodView):

    def get(self):
        # if g.interest is set, use that, else use first public interest
        if g.interest:
            values = {'interest' : g.interest}
        else:
            interest = Interest.query.filter_by(public=True).first()
            values = {'interest' : interest.interest}

        # redirect to routes page
        return redirect(url_for('frontend.routes', **values))

frontend_view = Index.as_view('index')
bp.add_url_rule('/', view_func=frontend_view, methods=['GET',])
bp.add_url_rule('/<interest>', view_func=frontend_view, methods=['GET',])


# ----------------------------------------------------------------------
def check_permission(checkinterest):
    if debug: print('frontend.check_permission()')

    # must be public if user not logged in
    filters = {}
    only_public = not current_user.is_authenticated
    if only_public:
        filters['public'] = True

    # g.interest initialized in runningroutes.create_app.pull_interest
    # g.interest contains slug, pull in interest db entry. If not found, no permission granted
    interest = Interest.query.filter_by(interest=checkinterest, **filters).one_or_none()
    if not interest:
        return False

    # if this is a public interest, we're good here
    if interest.public:
        return True

    # not a public interest -- we need to check more deeply

    # is someone logged in with ROLE_SUPER_ADMIN role? They're good
    superadmin = Role.query.filter_by(name=ROLE_SUPER_ADMIN).one()
    if superadmin in current_user.roles:
        return True

    # if they're not logged in with ROLE_ROUTES_ADMIN role, they're bad
    routesadmin = Role.query.filter_by(name=ROLE_ROUTES_ADMIN).one()
    if not routesadmin in current_user.roles:
        return False

    # current_user has ROLE_ROUTES_ADMIN. Can this user access current interest?
    if interest in current_user.interests:
        return True
    else:
        return False

#######################################################################
# view for user main runningroutes
#######################################################################
class UserRoutes(MethodView):

    # ----------------------------------------------------------------------
    def permission(self):
        return check_permission(g.interest)

    # ----------------------------------------------------------------------
    def beforequery(self):
        if debug: print('UserRoutes.beforequery()')

        self.queryparams = {}

        # not sure what it means if interest can't be found at this point, but if so interest_id = 0 should return empty set
        linterest = localinterest()
        linterest_id = linterest.id if linterest else 0
        self.queryparams['interest_id'] = linterest_id

    # ----------------------------------------------------------------------
    def get(self):
        if not self.permission():
            db.session.rollback()
            abort(403)

        # set up parameters to query (set self.queryparams)
        self.beforequery()

        if request.path[-5:] != '/rest':
            return self._renderpage()
        else:
            return self._retrieverows()

    def _renderpage(self):
        iconmap = IconMap.query.filter_by(**self.queryparams).one_or_none()
        if iconmap:
            iconmapname = iconmap.page_title
        else:
            iconmapname = 'Icon Map'

        return render_template('frontend_routes.jinja2',
            pagename = 'Routes',
            iconmapname = iconmapname,
            assets_css = 'frontend_css',
            assets_js = 'frontendroutes_js',
            frontend_page = True,
        )


    def _retrieverows(self):
        routes = Route.query.filter_by(**self.queryparams).all()

        # this is a bit goofy but is trying to use googles geo FeatureCollection
        geo = {
            'type': 'FeatureCollection',
            'features': [],
        }

        # add points from database
        for route in routes:
            # skip inactive routes
            if not route.active: continue

            lat = route.latlng.split(',')[0];
            lng = route.latlng.split(',')[1];

            thisgeo = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lat, lng],
                    'properties': {
                                    'id': route.id,
                                    'name': route.name,
                                    'distance': route.distance,
                                    'surface': route.surface,
                                    'gain': route.elevation_gain,
                                    'links': '', # placeholder - built on the client
                                    'description': route.description,
                                    'lat': lat,
                                    'lng': lng,
                                    'start': route.start_location,
                                    'latlng': route.latlng,
                                    'map': route.map,
                                    'fileid': route.gpx_file_id,
                    }
                }
            }
            geo['features'].append(thisgeo)

        # case insensitive string sort by name field
        geo['features'].sort(key=lambda item: item['geometry']['properties']['name'].lower())
        return jsonify(geo);

routes_view = UserRoutes.as_view('routes')
bp.add_url_rule('/<interest>/routes', view_func=routes_view, methods=['GET',])
bp.add_url_rule('/<interest>/routes/rest', view_func=routes_view, methods=['GET',])

#######################################################################
# view for user single route
#######################################################################

class UserRoute(MethodView):

    # ----------------------------------------------------------------------
    def permission(self, routeid):
        checkinterest = local2common_interest(Route.query.filter_by(id=routeid).one().interest).interest
        return check_permission(checkinterest)

    # ----------------------------------------------------------------------
    def get(self, thisid):

        if request.path[-5:] != '/rest':
            return self._renderpage(thisid)
        else:
            return self._retrieverows(thisid)

    # ----------------------------------------------------------------------
    def _renderpage(self, thisid):
        thisid = int(thisid)

        # normally id is specified
        # id of 0 means there must be fileid argument, meaning gpx_file_id)
        # this must have come from legacy version redirect
        if thisid != 0:
            route = Route.query.filter_by(id=thisid).one()
        else:
            fileid = request.args.get('fileid', None)
            if not fileid:
                db.session.rollback()
                abort(403)
            route = Route.query.filter_by(gpx_file_id=fileid).one()
            redirecturl = url_for('frontend.route', thisid=route.id)
            app.logger.info(
                'legacy redirect: {} {} > {}'.format(request.method, request.full_path, redirecturl))
            return redirect(redirecturl)

        if not self.permission(route.id):
            db.session.rollback()
            abort(403)

        return render_template('frontend_route.jinja2',
                               pagename = 'Route',
                               assets_css = 'frontend_css',
                               assets_js = 'frontendroute_js',
                               frontend_page = True,
                               title = '{} - {} miles - {}'.format(route.name, route.distance, route.surface),
                               description = route.description,
                               elevation_gain = route.elevation_gain,
                               turns_link = url_for('frontend.turns', thisid=route.id),
                               gpx_link = url_for('frontend.gpxdownload', thisid=route.id),
                               route_id = route.id,
                               startloc = quote(route.start_location),
                               )

    # ----------------------------------------------------------------------
    def _retrieverows(self, thisid):
        route = Route.query.filter_by(id=thisid).one()
        routefile = get_fidfile(route.path_file_id)

        # verify access to group/interest is allowed, abort otherwise
        if not self.permission(route.id):
            db.session.rollback()
            abort(403)

        # process file and return data
        route_csv = DictReader(routefile['contents'])

        justpath = []
        ftpermeter = 3.280839895
        ele = 0

        for row in route_csv:
            # row.ele is in meters -- use feet by default
            ele = float(row['ele']) * ftpermeter
            # if ( parameters.metric ):
            #     ele = +row['ele'];
            # else:
            #     ele = +row['ele'] * ftpermeter;

            justpath.append( [row['lat'], row['lng'], float('{0:.1f}'.format(ele))] )

        return jsonify({'status' : 'success', 'path':justpath})

route_view = UserRoute.as_view('route')
bp.add_url_rule('/route/<thisid>', view_func=route_view, methods=['GET', ])
bp.add_url_rule('/route/<thisid>/rest', view_func=route_view, methods=['GET', ])

#######################################################################
# view for turns
#######################################################################

class UserTurns(MethodView):

    # ----------------------------------------------------------------------
    def permission(self, routeid):
        checkinterest = local2common_interest(Route.query.filter_by(id=routeid).one().interest).interest
        return check_permission(checkinterest)

    # ----------------------------------------------------------------------
    def get(self, thisid):

        if request.path[-5:] != '/rest':
            return self._renderpage(thisid)
        else:
            return self._retrieverows(thisid)

    # ----------------------------------------------------------------------
    def _renderpage(self, thisid):
        thisid = int(thisid)

        # normally id is specified
        # id of 0 means there must be fileid argument, meaning gpx_file_id)
        # this must have come from legacy version redirect
        if thisid != 0:
            route = Route.query.filter_by(id=thisid).one()
        else:
            fileid = request.args.get('fileid', None)
            if not fileid:
                db.session.rollback()
                abort(403)
            route = Route.query.filter_by(gpx_file_id=fileid).one()
            redirecturl = url_for('frontend.turns', thisid=route.id)
            app.logger.info(
                'legacy redirect: {} {} > {}'.format(request.method, request.full_path, redirecturl))
            return redirect(redirecturl)

        if not self.permission(route.id):
            db.session.rollback()
            abort(403)

        return render_template('frontend_turns.jinja2',
                               pagename = 'Turns',
                               assets_css = 'frontend_css',
                               assets_js = 'frontendturns_js',
                               frontend_page = True,
                               title = '{} - {} miles - {}'.format(route.name, route.distance, route.surface),
                               description = route.description,
                               elevation_gain = route.elevation_gain,
                               route_link = url_for('frontend.route', thisid=route.id),
                               gpx_link = url_for('frontend.gpxdownload', thisid=route.id),
                               route_id = route.id,
                               startloc = quote(route.start_location),
                               )

    # ----------------------------------------------------------------------
    def _retrieverows(self, thisid):
        route = Route.query.filter_by(id=thisid).one()

        # verify access to group/interest is allowed, abort otherwise
        if not self.permission(route.id):
            db.session.rollback()
            abort(403)

        # process file and return data
        if route.turns:
            justturns = route.turns.split('\n')
        else:
            justturns = []

        return jsonify({'status' : 'success', 'turns':justturns})

turns_view = UserTurns.as_view('turns')
bp.add_url_rule('/turns/<thisid>', view_func=turns_view, methods=['GET', ])
bp.add_url_rule('/turns/<thisid>/rest', view_func=turns_view, methods=['GET', ])

class UserDownloadGpxFile(MethodView):

    def get(self, thisid):
        route = Route.query.filter_by(id=thisid).one()
        gps_fid = route.gpx_file_id
        thefile = Files.query.filter_by(fileid=gps_fid).one()
        
        mainfolder = current_app.config['APP_FILE_FOLDER']
        groupfolder = join(mainfolder, local2common_interest(thefile.interest).interest)
        filepath = join(groupfolder, gps_fid)

        return send_file(
            filepath, 
            mimetype=thefile.mimetype, 
            as_attachment=True, 
            download_name=thefile.filename
        )

download_gpxfile_view = UserDownloadGpxFile.as_view('gpxdownload')
bp.add_url_rule('/gpxdownload/<thisid>', view_func=download_gpxfile_view, methods=['GET',])

