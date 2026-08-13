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

# jquery
jq_ver = '3.7.1'
jq_ui_ver = '1.14.2'

# dataTables
dt_datatables_ver = '2.3.8-pkgs-jqui'
# dt_editor_plugin_fieldtype_ver = '?'

# select2
# NOTE: patch to jquery ui required, see https://github.com/select2/select2/issues/1246#issuecomment-17428249
# currently in datatables.js
s2_ver = '4.0.13'

# smartmenus
sm_ver = '1.1.1'

# yadcf
yadcf_ver = '2.0.1.beta.9.louking.3'
yadcf_suffix = '-2.0'

lodash_ver = '4.17.21'      # lodash.js (see https://lodash.com)
d3_ver = '7.1.1'            # d3js.org (see https://d3js.org/)
d3_tip_ver = '1.1'          # https://github.com/VACLab/d3-tip

frontend_common_js = Bundle(
    f'js/jQuery-{jq_ver}/jquery-{jq_ver}.js',
    f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.js',

    f'js/lodash-{lodash_ver}/lodash.js',
    f'js/smartmenus-{sm_ver}/jquery.smartmenus.js',

    # datatables / yadcf
    f'js/yadcf-{yadcf_ver}/jquery.dataTables.yadcf{yadcf_suffix}.js',
    f'js/DataTables-{dt_datatables_ver}/datatables.js',

    # select2 is required for use by Editor forms and interest navigation
    f'js/select2-{s2_ver}/js/select2.full.js',
    # the order here is important
    'js/FieldType-Select2/editor.select2-v4.js',

    # d3
    f'js/d3-{d3_ver}/d3.js',
    f'js/d3-tip-{d3_tip_ver}/d3-tip.js',

    'layout.js',

    'utils.js',

    'mutex-promise.js',                     # from loutilities
    'datatables.js',  # from loutilities
    'datatables.dataRender.ellipsis.js',  # from loutilities
    'editor.buttons.editrefresh.js',  # from loutilities

    filters='rjsmin',
    output='gen/frontendcommon.js',
)

frontend_routes = Bundle(
    'frontend/runningroutes.js',

    filters='rjsmin',
    output='gen/frontendroutes.js',
)

frontend_route = Bundle(
    'frontend/runningroute-route.js',

    filters='rjsmin',
    output='gen/frontendroute.js',
)

frontend_turns = Bundle(
    'frontend/runningroute-turns.js',

    filters='rjsmin',
    output='gen/frontendturns.js',
)

frontend_locations = Bundle(
    'frontend/iconmap.js',

    filters='rjsmin',
    output='gen/frontendlocations.js',
)


asset_bundles = {

    'frontendroutes_js': Bundle(
        frontend_common_js,
        frontend_routes,
        ),

    'frontendroute_js': Bundle(
        frontend_common_js,
        frontend_route,
        ),

    'frontendturns_js': Bundle(
        frontend_common_js,
        frontend_turns,
        ),

    'frontendlocations_js': Bundle(
        frontend_common_js,
        frontend_locations,
        ),

    'frontend_css': Bundle(
        f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.css',
        f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.structure.css',
        f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.theme.css',
        
        f'js/DataTables-{dt_datatables_ver}/datatables.css',

        f'js/select2-{s2_ver}/css/select2.css',
        f'js/yadcf-{yadcf_ver}/jquery.dataTables.yadcf.css',

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
        f'js/jQuery-{jq_ver}/jquery-{jq_ver}.js',
        f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.js',

        f'js/smartmenus-{sm_ver}/jquery.smartmenus.js',
        f'js/lodash-{lodash_ver}/lodash.js',

        f'js/DataTables-{dt_datatables_ver}/datatables.js',
        f'js/yadcf-{yadcf_ver}/jquery.dataTables.yadcf{yadcf_suffix}.js',

        # select2 is required for use by Editor forms and interest navigation
        f'js/select2-{s2_ver}/js/select2.full.js',
        # the order here is important
        'js/FieldType-Select2/editor.select2-v4.js',

        # d3
        f'js/d3-{d3_ver}/d3.js',

        'admin/layout.js',
        'layout.js',

        'utils.js',

        # must be before datatables
        'user/admin/beforedatatables.js',       # from loutilities
        'mutex-promise.js',                     # from loutilities

        'datatables.js',                        # from loutilities
        'datatables.dataRender.ellipsis.js',    # from loutilities
        'editor.buttons.editrefresh.js',        # from loutilities

        'admin/groups.js',          # must be after datatables.js

        'admin/runningroute-admin.js',

        output='gen/admin.js',
        filters='rjsmin',
        ),

    'admin_css': Bundle(
       f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.css',
       f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.structure.css',
       f'js/jquery-ui-{jq_ui_ver}.custom/jquery-ui.theme.css',

       f'js/DataTables-{dt_datatables_ver}/datatables.css',

       f'js/smartmenus-{sm_ver}/css/sm-core-css.css',
       f'js/smartmenus-{sm_ver}/css/sm-blue/sm-blue.css',
       
       'js/select2-{ver}/css/select2.css'.format(ver=s2_ver),
       f'js/yadcf-{yadcf_ver}/jquery.dataTables.yadcf.css',

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
