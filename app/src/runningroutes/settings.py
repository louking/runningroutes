###########################################################################################
# settings - define default, test and production settings
#
#       Date            Author          Reason
#       ----            ------          ------
#       07/18/18        Lou King        Create
#
#   Copyright 2018 Lou King.  All rights reserved
#
###########################################################################################
'''
settings - define default, test and production settings

see http://flask.pocoo.org/docs/1.0/config/?highlight=production#configuration-best-practices
'''

# standard
import logging

# homegrown
from loutilities.configparser import getitems


class Config(object):
    DEBUG = False
    TESTING = False

    # default database
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/binds/
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_BINDS = {
        'users': 'sqlite:///:memory:',
    }

    # logging
    LOGGING_LEVEL_FILE = logging.INFO
    LOGGING_LEVEL_MAIL = logging.ERROR

    # flask-security configuration -- see https://pythonhosted.org/Flask-Security/configuration.html
    SECURITY_TRACKABLE = True
    SECURITY_DEFAULT_REMEMBER_ME = True
    # SECURITY_LOGIN_URL = False
    # SECURITY_LOGOUT_URL = False

    # javascript configuration
    # APP_JS_CONFIG = 'contracts-prod-config.js'

    # avoid warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # branding
    THISAPP_PRODUCTNAME = '<span class="brand-all"><span class="brand-left">route</span><span class="brand-right">tility</span></span>'
    THISAPP_PRODUCTNAME_TEXT = 'routetility'


class Testing(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False

    # need to set SERVER_NAME to something, else get a RuntimeError about not able to create URL adapter
    # must have following line in /etc/hosts or C:\Windows\System32\drivers\etc\hosts file
    #   127.0.0.1 dev.localhost
    SERVER_NAME = 'dev.localhost'

    # need a default secret key - in production replace by config file
    SECRET_KEY = "<test secret key>"

    # required by flask_security.utils.get_hmac() whenever SECURITY_PASSWORD_HASH needs a salt
    # (e.g. the default 'argon2'); normally supplied by config/runningroutes.cfg
    SECURITY_PASSWORD_SALT = "<test password salt>"

    # fake  credentials
    GOOGLE_OAUTH_CLIENT_ID = 'fake-client-id'
    GOOGLE_OAUTH_CLIENT_SECRET = 'fake-client-secret'

    # need to allow logins in flask-security. see https://github.com/mattupstate/flask-security/issues/259
    LOGIN_DISABLED = False

    # required by loutilities.user.applogging.setlogging(), normally supplied by config/users.cfg
    EXCEPTION_EMAIL = 'test-exceptions@example.com'

    # required by create_app() to look up the Application row for g.loutility, normally supplied by
    # config/runningroutes.cfg -- must match the Application.application value seeded by conftest.py
    APP_LOUTILITY = 'routes'

    # required by create_app()'s productname formatting, normally supplied by config/users.cfg
    SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = "{productname}: please reset your password"
    SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = "{productname}: your password has been changed"
    SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE = "{productname}: your password has been reset"

    # fake google maps credentials -- googlemaps.Client() only checks the "AIza" prefix at
    # construction time, never makes a network call unless a request method is actually invoked.
    # required because locations.py, views/admin/routes.py, views/admin/icons.py,
    # views/frontend/frontend.py, and views/frontend/icons.py all read this (and construct a
    # GmapsLoc/Client) at *module import time*, which happens as a side effect of create_app()
    # registering the admin/frontend blueprints -- see test/conftest.py
    GMAPS_ELEV_API_KEY = 'AIzaFakeTestKey0000000000000000000'
    GMAPS_API_KEY = 'AIzaFakeTestKey0000000000000000000'

    # required at import time by views/admin/routes.py (module-level GeoDistance(APP_EARTH_RADIUS))
    APP_EARTH_RADIUS = 6369.665

    # used by views/admin/routes.py's RunningRoutesFiles.upload()/RunningRoutesTable.snaploc()
    APP_MAX_DIST_INTERVAL = 50
    APP_ROUTE_LOC_EPSILON = 20
    APP_ELEV_UPTHRESHOLD = 6
    APP_ELEV_DOWNTHRESHOLD = 6
    APP_SMOOTHING_WINDOW = 5

    # used by geo.GmapsLoc.get_location() (locations.py/views callers) and dbinit.init_db()
    GMAPS_CACHE_LIMIT = 30
    MAP_ICON_WIDTH = 20
    APP_JS_CONFIG = 'test-config.js'

    # fake owner credentials for dbinit.init_db()
    APP_OWNER = 'test-owner@example.com'
    APP_OWNER_PW = 'test-owner-password'
    APP_OWNER_NAME = 'Test Owner'
    APP_OWNER_GIVEN_NAME = 'Test'


class RealDb(Config):
    def __init__(self, configfiles):
        if type(configfiles) == str:
            configfiles = [configfiles]

        # connect to database based on configuration
        config = {}
        for configfile in configfiles:
            config.update(getitems(configfile, 'database'))
        dbuser = config['dbuser']
        with open(f'/run/secrets/appdb-password') as pw:
            password = pw.readline().strip()
        dbserver = config['dbserver']
        dbname = config['dbname']
        db_uri = f'mysql+pymysql://{dbuser}:{password}@{dbserver}/{dbname}'
        self.SQLALCHEMY_DATABASE_URI = db_uri
        
        # when user database is available, add bind
        if 'usersdbname' in config:
            # https://flask-sqlalchemy.palletsprojects.com/en/2.x/binds/
            usersdbuser = config['usersdbuser']
            with open(f'/run/secrets/users-password') as pw:
                userspassword = pw.readline().strip()
            usersdbserver = config['usersdbserver']
            usersdbname = config['usersdbname']
            usersdb_uri = f'mysql+pymysql://{usersdbuser}:{userspassword}@{usersdbserver}/{usersdbname}'
            self.SQLALCHEMY_BINDS = {
                'users': usersdb_uri
            }

class Development(RealDb):
    DEBUG = True

class Production(RealDb):
    pass


