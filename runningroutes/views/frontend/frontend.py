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
from flask import render_template
from flask.views import MethodView

# home grown
from . import bp
from loutilities.flask_helpers.blueprints import add_url_rules

#######################################################################
class Index(MethodView):
#######################################################################
    url_rules = {
                'index': ['/',('GET',)],
                }

    def get(self):
        return render_template('index.jinja2')

#----------------------------------------------------------------------
add_url_rules(bp, Index)
#----------------------------------------------------------------------
