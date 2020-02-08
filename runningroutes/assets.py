###########################################################################################
# assets - javascript and css asset handling
#
#       Date            Author          Reason
#       ----            ------          ------
#       11/16/18        Lou King        Create
#
#   Copyright 2018 Lou King.  All rights reserved
#
###########################################################################################

'''
assets - javascript and css asset handling
===================================================
'''

from flask_assets import Bundle, Environment
from runningroutes import app

# jquery
jq_ver = '3.4.1'
jq_ui_ver = '1.12.1'

# dataTables
dt_datatables_ver = '1.10.20'
dt_editor_ver = '1.9.2'
dt_buttons_ver = '1.6.1'
dt_colvis_ver = '1.6.1'
dt_fixedcolumns_ver = '3.3.0'
dt_select_ver = '1.3.1'
dt_responsive_ver = '2.2.3'
# dt_editor_plugin_fieldtype_ver = '?'

# select2
# NOTE: patch to jquery ui required, see https://github.com/select2/select2/issues/1246#issuecomment-17428249
# currently in datatables.js
s2_ver = '4.0.12'

# yadcf
yadcf_ver = '0.9.4.beta.33'

moment_ver = '2.24.0'       # moment.js (see https://momentjs.com/)
lodash_ver = '4.17.15'      # lodash.js (see https://lodash.com)
d3_ver = '5.14.2'           # d3js.org (see https://d3js.org/)
d3_tip_ver = '1.1'          # https://github.com/VACLab/d3-tip

frontend_common_js = Bundle(
    'js/jquery-{ver}/jquery.js'.format(ver=jq_ver),
    'js/jquery-ui-{ver}.custom/jquery-ui.js'.format(ver=jq_ui_ver),

    'js/lodash-{ver}/lodash.js'.format(ver=lodash_ver),

    # datatables / yadcf
    'js/DataTables-{ver}/js/jquery.dataTables.js'.format(ver=dt_datatables_ver),
    'js/DataTables-{ver}/js/dataTables.jqueryui.js'.format(ver=dt_datatables_ver),
    'js/yadcf-{ver}/jquery.dataTables.yadcf.js'.format(ver=yadcf_ver),

    'js/FixedColumns-{ver}/js/dataTables.fixedColumns.js'.format(ver=dt_fixedcolumns_ver),
    'js/Responsive-{ver}/js/dataTables.responsive.js'.format(ver=dt_responsive_ver),
    'js/Responsive-{ver}/js/responsive.jqueryui.js'.format(ver=dt_responsive_ver),

    'js/Editor-{ver}/js/dataTables.editor.js'.format(ver=dt_editor_ver),
    'js/Editor-{ver}/js/editor.jqueryui.js'.format(ver=dt_editor_ver),

    'js/Select-{ver}/js/dataTables.select.js'.format(ver=dt_select_ver),

    # select2 is required for use by Editor forms and interest navigation
    'js/select2-{ver}/js/select2.full.js'.format(ver=s2_ver),
    # the order here is important
    'js/FieldType-Select2/editor.select2.js',

    # date time formatting
    'js/moment-{ver}/moment.js'.format(ver=moment_ver),

    # d3
    'js/d3-{ver}/d3.v5.js'.format(ver=d3_ver),
    'js/d3-tip-{ver}/d3-tip.js'.format(ver=d3_tip_ver),

    'layout.js',

    'utils.js',

    'datatables.js',  # from loutilities
    'datatables.dataRender.ellipsis.js',  # from loutilities
    'editor.buttons.editrefresh.js',  # from loutilities

    filters='jsmin',
    output='gen/frontendcommon.js',
)

google_maps = Bundle(
    'https://maps.google.com/maps/api/js?key={}'.format(app.config['GMAPS_API_KEY']),
)

frontend_routes = Bundle(
    'frontend/runningroutes.js',

    filters='jsmin',
    output='gen/frontendroutes.js',
)

frontend_route = Bundle(
    'frontend/runningroute-route.js',

    filters='jsmin',
    output='gen/frontendroute.js',
)

frontend_turns = Bundle(
    'frontend/runningroute-turns.js',

    filters='jsmin',
    output='gen/frontendturns.js',
)

asset_bundles = {

    'frontendroutes_js': Bundle(
        frontend_common_js,
        google_maps,
        frontend_routes,
        ),

    'frontendroute_js': Bundle(
        frontend_common_js,
        google_maps,
        frontend_route,
        ),

    'frontendturns_js': Bundle(
        frontend_common_js,
        frontend_turns,
        ),

    'frontend_css': Bundle(
        'js/jquery-ui-{ver}.custom/jquery-ui.css'.format(ver=jq_ui_ver),
        'js/jquery-ui-{ver}.custom/jquery-ui.structure.css'.format(ver=jq_ui_ver),
        'js/jquery-ui-{ver}.custom/jquery-ui.theme.css'.format(ver=jq_ui_ver),
        'js/DataTables-{ver}/css/dataTables.jqueryui.css'.format(ver=dt_datatables_ver),
        'js/Buttons-{ver}/css/buttons.jqueryui.css'.format(ver=dt_buttons_ver),
        'js/FixedColumns-{ver}/css/fixedColumns.jqueryui.css'.format(ver=dt_fixedcolumns_ver),
        'js/Responsive-{ver}/css/responsive.dataTables.css'.format(ver=dt_responsive_ver),
        'js/Responsive-{ver}/css/responsive.jqueryui.css'.format(ver=dt_responsive_ver),
        'js/Editor-{ver}/css/editor.jqueryui.css'.format(ver=dt_editor_ver),
        'js/Select-{ver}/css/select.jqueryui.css'.format(ver=dt_select_ver),
        'js/select2-{ver}/css/select2.css'.format(ver=s2_ver),
        'js/yadcf-{ver}/jquery.dataTables.yadcf.css'.format(ver=yadcf_ver),

        'datatables.css',  # from loutilities
        'editor.css',  # from loutilities
        'filters.css',  # from loutilities
        'branding.css',  # from loutilities

        'frontend/runningroutes.css',
        'frontend/runningroute-route.css',
        'frontend/runningroute-turns.css',
        'style.css',

        output='gen/frontend.css',
        # cssrewrite helps find image files when ASSETS_DEBUG = False
        filters=['cssrewrite', 'cssmin'],
        ),

    'admin_js': Bundle(
        'js/jquery-{ver}/jquery.js'.format(ver=jq_ver),
        'js/jquery-ui-{ver}.custom/jquery-ui.js'.format(ver=jq_ui_ver),

        'js/lodash-{ver}/lodash.js'.format(ver=lodash_ver),

        'js/DataTables-{ver}/js/jquery.dataTables.js'.format(ver=dt_datatables_ver),
        'js/DataTables-{ver}/js/dataTables.jqueryui.js'.format(ver=dt_datatables_ver),
        'js/yadcf-{ver}/jquery.dataTables.yadcf.js'.format(ver=yadcf_ver),

        'js/Buttons-{ver}/js/dataTables.buttons.js'.format(ver=dt_buttons_ver),
        'js/Buttons-{ver}/js/buttons.jqueryui.js'.format(ver=dt_buttons_ver),
        'js/Buttons-{ver}/js/buttons.html5.js'.format(ver=dt_buttons_ver),
        'js/Buttons-{ver}/js/buttons.colVis.js'.format(ver=dt_colvis_ver), 

        'js/FixedColumns-{ver}/js/dataTables.fixedColumns.js'.format(ver=dt_fixedcolumns_ver),

        'js/Editor-{ver}/js/dataTables.editor.js'.format(ver=dt_editor_ver),
        'js/Editor-{ver}/js/editor.jqueryui.js'.format(ver=dt_editor_ver),

        'js/Select-{ver}/js/dataTables.select.js'.format(ver=dt_select_ver),

        # select2 is required for use by Editor forms and interest navigation
        'js/select2-{ver}/js/select2.full.js'.format(ver=s2_ver),
        # the order here is important
        'js/FieldType-Select2/editor.select2.js',

        # date time formatting for datatables editor, per https://editor.datatables.net/reference/field/datetime
        'js/moment-{ver}/moment.js'.format(ver=moment_ver),

        # d3
        'js/d3-{ver}/d3.v5.js'.format(ver=d3_ver),

        'admin/layout.js',
        'layout.js',

        'utils.js',

        'datatables.js',                        # from loutilities
        'datatables.dataRender.ellipsis.js',    # from loutilities
        'editor.buttons.editrefresh.js',        # from loutilities

        'admin/groups.js',          # must be after datatables.js

        'admin/runningroute-admin.js',

        output='gen/admin.js',
        filters='jsmin',
        ),

    'admin_css': Bundle(
        'js/jquery-ui-{ver}.custom/jquery-ui.css'.format(ver=jq_ui_ver),
        'js/jquery-ui-{ver}.custom/jquery-ui.structure.css'.format(ver=jq_ui_ver),
        'js/jquery-ui-{ver}.custom/jquery-ui.theme.css'.format(ver=jq_ui_ver),
        'js/DataTables-{ver}/css/dataTables.jqueryui.css'.format(ver=dt_datatables_ver),
        'js/Buttons-{ver}/css/buttons.jqueryui.css'.format(ver=dt_buttons_ver),
        'js/FixedColumns-{ver}/css/fixedColumns.jqueryui.css'.format(ver=dt_fixedcolumns_ver),
        'js/Editor-{ver}/css/editor.jqueryui.css'.format(ver=dt_editor_ver),
        'js/Select-{ver}/css/select.jqueryui.css'.format(ver=dt_select_ver),
        'js/select2-{ver}/css/select2.css'.format(ver=s2_ver),
        'js/yadcf-{ver}/jquery.dataTables.yadcf.css'.format(ver=yadcf_ver),

        'datatables.css',   # from loutilities
        'editor.css',       # from loutilities
        'filters.css',      # from loutilities
        'branding.css',     # from loutilities

        'style.css',
        'admin/style.css',

        output='gen/admin.css',
        # cssrewrite helps find image files when ASSETS_DEBUG = False
        filters=['cssrewrite', 'cssmin'],
        )
}

asset_env = Environment()
