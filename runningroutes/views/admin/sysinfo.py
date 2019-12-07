###########################################################################################
# sysinfo - debug views for web application
#
#       Date            Author          Reason
#       ----            ------          ------
#       07/08/18        Lou King        Create
#
#   Copyright 2018 Lou King
#
###########################################################################################

# standard

# pypi
from flask import current_app, make_response, request, render_template, session
from flask.views import MethodView
from flask_security import roles_accepted

# home grown
from . import bp
from runningroutes.models import db
from runningroutes.version import __version__
from loutilities.flask_helpers.blueprints import add_url_rules

class testException(Exception): pass

thisversion = __version__

#######################################################################
class ViewSysinfo(MethodView):
#######################################################################
    # decorators = [lambda f: roles_accepted('super-admin', 'event-admin')(f)]
    url_rules = {
                'sysinfo': ['/sysinfo',('GET',)],
                }

    #----------------------------------------------------------------------
    def get(self):
    #----------------------------------------------------------------------
        try:
            # commit database updates and close transaction
            db.session.commit()
            return render_template('sysinfo.jinja2',pagename='About',version=thisversion)
        
        except:
            # roll back database updates and close transaction
            db.session.rollback()
            raise
#----------------------------------------------------------------------
add_url_rules(bp, ViewSysinfo)
# sysinfo_view = roles_accepted('super-admin', 'event-admin')(ViewSysinfo.as_view('sysinfo'))
# current_app.add_url_rule('/sysinfo',view_func=sysinfo_view,methods=['GET'])
#----------------------------------------------------------------------

#######################################################################
class ViewDebug(MethodView):
#######################################################################
    decorators = [lambda f: roles_accepted('super-admin')(f)]
    url_rules = {
                'debug': ['/_debuginfo',('GET',)],
                }
    #----------------------------------------------------------------------
    def get(self):
    #----------------------------------------------------------------------
        try:
            appconfigpath = getattr(current_app,'configpath','<not set>')
            appconfigtime = getattr(current_app,'configtime','<not set>')

            # collect groups of system variables                        
            sysvars = []
            
            # collect current_app.config variables
            configkeys = list(current_app.config.keys())
            configkeys.sort()
            appconfig = []
            for key in configkeys:
                value = current_app.config[key]
                if True:    # maybe check for something else later
                    if key in ['SQLALCHEMY_DATABASE_URI', 'SECRET_KEY', 'GOOGLE_OAUTH_CLIENT_ID', 'GOOGLE_OAUTH_CLIENT_SECRET']:
                        value = '<obscured>'
                appconfig.append({'label':key, 'value':value})
            sysvars.append(['current_app.config',appconfig])
            
            # collect flask.session variables
            sessionkeys = list(session.keys())
            sessionkeys.sort()
            sessionconfig = []
            for key in sessionkeys:
                value = session[key]
                sessionconfig.append({'label':key, 'value':value})
            sysvars.append(['flask.session',sessionconfig])
            
            # commit database updates and close transaction
            db.session.commit()
            return render_template('sysinfo.jinja2',pagename='Debug',
                                         version=thisversion,
                                         configpath=appconfigpath,
                                         configtime=appconfigtime,
                                         sysvars=sysvars,
                                         # owner=owner_permission.can(),
                                         inhibityear=True,inhibitclub=True)
        
        except:
            # roll back database updates and close transaction
            db.session.rollback()
            raise
#----------------------------------------------------------------------
add_url_rules(bp, ViewDebug)
# debuginfo_view = roles_accepted('super-admin')(ViewDebug.as_view('debug'))
# # debuginfo_view = ViewDebug.as_view('debug')
# current_app.add_url_rule('/_debuginfo',view_func=debuginfo_view,methods=['GET'])
#----------------------------------------------------------------------

#######################################################################
class TestException(MethodView):
#######################################################################
    decorators = [lambda f: roles_accepted('super-admin')]
    url_rules = {
                'testexception': ['/xcauseexception',('GET',)],
                }
    #----------------------------------------------------------------------
    def get(self):
    #----------------------------------------------------------------------
        try:
            raise testException
                    
        except:
            # roll back database updates and close transaction
            db.session.rollback()
            raise
#----------------------------------------------------------------------
# exception_view = roles_accepted('super-admin')(TestException.as_view('testexception'))
# current_app.add_url_rule('/xcauseexception',view_func=exception_view,methods=['GET'])
#----------------------------------------------------------------------
