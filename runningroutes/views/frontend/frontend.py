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

# pypi
from flask import g, redirect, url_for
from flask.views import MethodView
from flask_security import current_user
from dominate.tags import div, span, script

# home grown
from . import bp
from runningroutes import app
from loutilities.tables import DbCrudApiRolePermissions
from runningroutes.models import db, Route, Interest, Role, ROLE_SUPER_ADMIN, ROLE_INTEREST_ADMIN

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

#######################################################################
# api endpoint for runningroutes
#######################################################################
class UserRoutes(DbCrudApiRolePermissions):
    # ----------------------------------------------------------------------
    def permission(self):
        if debug: print('UserRoutes.permission()')

        # must be public if user not logged in
        filters = {}
        only_public = not current_user.is_authenticated
        if only_public:
            filters['public'] = True

        # g.interest initialized in runningroutes.create_app.pull_interest
        # g.interest contains slug, pull in interest db entry. If not found, no permission granted
        self.interest = Interest.query.filter_by(interest=g.interest, **filters).one_or_none()
        if not self.interest:
            return False

        # if this is a public interest, we're good here
        if self.interest.public:
            return True

        # not a public interest -- we need to check more deeply

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

    # ----------------------------------------------------------------------
    def beforequery(self):
        if debug: print('UserRoutes.beforequery()')

        # g.interest is set in runningroutes.__init__.pull_interest
        interest = Interest.query.filter_by(interest=g.interest).one_or_none()
        # not sure if interest can't be found at this point, but if so interest_id = 0 should return empty set
        interest_id = interest.id if interest else 0
        self.queryparams['interest_id'] = interest_id

# options for yadcf
yadcf_options = [
          { 'column_selector': 'distance:name',
            'filter_type': 'range_number',
            'filter_container_id': 'external-filter-distance',
          },
          { 'column_selector': 'surface:name',
            'filter_container_id': 'external-filter-surface',
            'select_type': 'select2',
            'filter_reset_button_text' : False,
            'select_type_options': {
                'width': '100px',
                'allowClear': True,  # show 'x' (remove) next to selection inside the select itself
                'minimumResultsForSearch': 'Infinity',  # no search box
                'placeholder': {
                    'id': -1,
                    'text': 'Select surface',
                },
            },
          },
          # { 'column_selector': 'lat:name',
          #   'filter_type': 'range_number',
          #   'filter_container_id': 'external-filter-bounds-lat',
          # },
          # { 'column_selector': 'lng:name',
          #   'filter_type': 'range_number',
          #   'filter_container_id': 'external-filter-bounds-lng',
          # },
    ];

# build up pretable html
visiblefilters = div(_class='external-filter filter-container')
with visiblefilters:
    with visiblefilters.add(div(_class='filter-item')):
        span('Distance (miles)', _class='label')
        span(id='external-filter-distance', _class='filter')
    with visiblefilters.add(div(_class='filter-item')):
        span('Surface', _class='label')
        span(id='external-filter-surface', _class='filter')
hiddenfilters = div(_class='external-filter', style='display: none;')
with hiddenfilters:
    span(id='external-filter-bounds-lat', _class='filter')
    span(id='external-filter-bounds-lng', _class='filter')
themap = div(id='runningroutes-map')
prehtml = '\n'.join([
                        visiblefilters.render(),
                        hiddenfilters.render(),
                        themap.render(),
                    ])

frontend_dbattrs = 'id,__skip__,__skip__,name,distance,start_location,latlng,surface,elevation_gain,map,gpx_file_id,path_file_id,description,turns,active'.split(',')
frontend_formfields = 'rowid,loc,links,name,distance,location,latlng,surface,elevation_gain,map,gpx_file_id,path_file_id,description,turns,active'.split(',')
frontend_dbmapping = dict(list(zip(frontend_dbattrs, frontend_formfields)))
frontend_formmapping = dict(list(zip(frontend_formfields, frontend_dbattrs)))

usertable = UserRoutes(app=bp,
                       db = db,
                       pagename = 'Routes',
                       template = 'frontend_routes.jinja2',
                       templateargs = {
                           'assets_css' : 'frontend_css',
                           'assets_js' : 'frontend_js',
                           'frontend_page' : True,
                       },
                       pretablehtml = prehtml,
                       model = Route,
                       idSrc = 'rowid',
                       rule = '/<interest>/routes',
                       endpoint = 'frontend.routes',
                       endpointvalues = {'interest':'<interest>'},
                       dbmapping = frontend_dbmapping,
                       formmapping = frontend_formmapping,
                       buttons = ['csv'],
                       yadcfoptions = yadcf_options,
                       clientcolumns =  [
                                           {'name': 'loc', 'data': 'loc', 'label': 'loc', 'className': "dt-body-center", 'defaultContent': ''}, # set in preDraw
                                           {'name': 'name', 'data': 'name', 'label': 'name'},
                                           {'name': 'distance', 'data': 'distance', 'label': 'miles', 'className': "dt-body-center"},
                                           {'name': 'surface', 'data': 'surface', 'label': 'surf', 'className': "dt-body-center"},
                                           {'name': 'elevation_gain', 'data': 'elevation_gain', 'label': 'elev gain', 'className': "dt-body-center", 'defaultContent': ''},
                                           {'name': 'turns', 'data': 'turns', 'label': 'elev gain', 'visible': False},
                                           {'name': 'links', 'data': 'links', 'label': '', 'orderable': False, 'render': {'eval':'render_links()'}},
                                           # {'name': 'lat', 'data': 'geometry.properties.lat', 'visible': False},
                                           # {'name': 'lng', 'data': 'geometry.properties.lng', 'visible': False},
        ])
usertable.register()
