###########################################################################################
# icons - frontend views for runningroutes database, icons management
#
#       Date            Author          Reason
#       ----            ------          ------
#       02/08/20        Lou King        Create
#
#   Copyright 2020 Lou King.  All rights reserved
###########################################################################################

# standard
from json import dumps
import xml.etree.ElementTree as ET

# pypi
from flask import g, jsonify, abort, request, render_template, current_app
from flask.views import MethodView
from markdown import markdown
from sqlalchemy import inspect

# homegrown
from . import bp
from .frontend import check_permission
from runningroutes import app
from runningroutes.models import db, Interest, IconLocation, IconMap
from runningroutes.geo import GmapsLoc
from runningroutes.files import get_fidfile

debug = False

# set up for google maps location management
gmaps = GmapsLoc(app.config['GMAPS_ELEV_API_KEY'])

#######################################################################
class IconLocationsApi(MethodView):

    # ----------------------------------------------------------------------
    def permission(self):
        return check_permission(g.interest)

    # ----------------------------------------------------------------------
    def beforequery(self):
        if debug: print('IconLocationsApi.beforequery()')

        self.queryparams = {}

        # g.interest is set in runningroutes.__init__.pull_interest
        interest = Interest.query.filter_by(interest=g.interest).one_or_none()
        # not sure if interest can't be found at this point, but if so interest_id = 0 should return empty set
        interest_id = interest.id if interest else 0
        self.queryparams['interest_id'] = interest_id

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
            return self._retrieverows(rest=True)

    #----------------------------------------------------------------------
    def _renderpage(self):
        iconmap = IconMap.query.filter_by(**self.queryparams).one_or_none()
        if iconmap:
            pagename = iconmap.page_title
            heading = markdown(iconmap.page_description, extensions=['md_in_html', 'attr_list']) if iconmap.page_description else ''
            # TODO: need configuration for mapcenter
            mapcenter = [39.431206, -77.415428]
        else:
            pagename = 'Icon Map'
            heading = ''
            mapcenter = [39.431206, -77.415428]

        features = self._retrieverows(rest=False)
        return render_template('frontend_locations.jinja2',
                               pagename = pagename,
                               heading = heading,
                               assets_css = 'frontend_css',
                               assets_js = 'frontendlocations_js',
                               mapcenter = mapcenter,
                               frontend_page = True,
                               features= features,
                               featuresjson=dumps(features)
        )

    #----------------------------------------------------------------------
    def _retrieverows(self, rest):
        '''

        :param rest: True if this is a rest request, False to just return features
        :return: json ( [feature, ...] ) if rest else [feature, ...]
            where:
                feature = {
                    'id'        : 'exc-{}'.format(exception.daterule.id),
                    'title'     : exception.shortDescr,
                    'start'     : date,
                    'exception' : exception.exception
                }
        '''
        if not g.interest:
            return jsonify ( { 'status': 'FAIL', 'code': 'no interest selected' } )

        locations = IconLocation.query.filter_by(**self.queryparams).all()

        features = []
        iconpath = {}
        scale = {}
        anchor = {}
        for location in locations:
            fid = location.icon.svg_file_id
            # get path
            if fid not in iconpath:
                # contents is list of lines in the file
                svgitem = ET.fromstring('\n'.join(get_fidfile(fid)['contents']))
                pathl = []
                scale[fid] = 1
                anchor[fid] = [0,0]
                for el in svgitem.iter():
                    # determine scale based on width vs. configured width
                    if el.tag.split('}')[1] == 'svg':
                        width = float(el.get('width'))
                        height = float(el.get('height'))
                        # if width not there assume square
                        if not width:
                            width = height
                        # height and width not there, so just leave scale at 1
                        if width:
                            scale[fid] = current_app.config['MAP_ICON_WIDTH'] / width
                        # set anchor based on height and width if present
                        anchor[fid][0] = scale[fid]*width/2 if width else 0
                        anchor[fid][1] = scale[fid]*height/2 if height else 0
                    # look past the {namespace} portion of the tag {namespace}path
                    if el.tag.split('}')[1] == 'path' and el.get('fill') != 'none':
                        pathl.append(el.get('d'))
                if len(pathl) != 1:
                    current_app.logger.debug('IconLocationsApi._retrieverows(): multiple paths found for svg file {}'.format(fid))
                path = ' '.join(pathl)
                iconpath[fid] = path
            loc = gmaps.get_location(location.location.location, location.location.id, app.config['GMAPS_CACHE_LIMIT'])
            latlng = loc['coordinates']
            feature = {
                'type' : 'Feature',
                'geometry' : {
                    'type' : 'Point',
                    'coordinates' : latlng,
                    'properties' : {
                        'name' : location.locname,
                        # 'icon' : get_fidfile( location.icon.svg_file_id )['contents'],
                        'iconattrs' : {c.key: getattr(location.icon, c.key)
                                       for c in inspect(location.icon).mapper.column_attrs
                                       if c.key != 'interest'},
                        'path' : iconpath[fid],
                        'scale' : scale[fid],
                        'anchor' : anchor[fid],
                        'loctext' : location.location_popup_text if location.location_popup_text else location.location.location,
                        'addl_text' : location.addl_text,
                        'type' : location.icon.icon if location.icon else None,
                        'subtype' : location.iconsubtype.iconsubtype if location.iconsubtype else None,
                        'phone' : location.phone,
                    }
                }
            }

            features.append( feature )

        if rest:
            # rest is called to load map page, so need to filter features
            return jsonify ( { 'features': [f for f in features if f['geometry']['properties']['iconattrs']['isShownInTable']] } )
        else:
            return features

locations_view = IconLocationsApi.as_view('locations')
bp.add_url_rule('/<interest>/locations', view_func=locations_view, methods=['GET',])
bp.add_url_rule('/<interest>/locations/rest', view_func=locations_view, methods=['GET',])

#######################################################################
class IconsFiles(MethodView):

   # ----------------------------------------------------------------------
    def get(self, fileid):
        if debug: print('IconsFiles.get() self = {}, fileid = {}'.format(self, fileid))
        return jsonify( {'svg': get_fidfile( fileid )['contents'],} )

iconimage = IconsFiles.as_view('iconimage')
bp.add_url_rule('/iconimage/<fileid>', view_func=iconimage, methods=['GET',])
