###########################################################################################
# runningroutes.wsgi - run the web application
#
#       Date            Author          Reason
#       ----            ------          ------
#       01/08/20        Lou King        Create
#
#   Copyright 2020 Lou King
###########################################################################################

import os, sys
from configparser import SafeConfigParser

# debug - information about python environment
# goes to /var/log/httpd/error_log, per http://modwsgi.readthedocs.io/en/develop/user-guides/debugging-techniques.html
if True:
    import platform
    print('started with python {}, {}'.format(platform.python_version(), platform.python_compiler()), file=sys.stderr)


# set configuration file, for here and for app
os.environ['CONFIG_FILE'] = 'runningroutes.cfg'

# get configuration
config = SafeConfigParser()
thisdir = os.path.dirname(__file__)
configpath = os.path.join(os.path.dirname(thisdir), 'runningroutes', 'config', os.environ['CONFIG_FILE'])
config.readfp(open(os.path.join(configpath)))
PROJECT_DIR = config.get('project', 'PROJECT_DIR')
# remove quotes if present
if PROJECT_DIR[0] == '"': PROJECT_DIR = PROJECT_DIR[1:-1]

# activate virtualenv
activate_this = os.path.join(PROJECT_DIR, 'bin', 'activate_this.py')
exec(compile(open(activate_this, "rb").read(), activate_this, 'exec'), dict(__file__=activate_this))
sys.path.append(PROJECT_DIR)
sys.path.append(thisdir)

# debug - which user is starting this?
# goes to /var/log/httpd/error_log, per http://modwsgi.readthedocs.io/en/develop/user-guides/debugging-techniques.html
if False:
    from getpass import getuser
    print('runningroutes user = {}'.format(getuser()), file=sys.stderr)

# from runningroutes import app as application
from runningroutes import create_app
from runningroutes.settings import Production
userconfigpath = os.path.join(os.path.dirname(thisdir), 'config', 'users.cfg')
# userconfigpath first so configpath can override
configfiles = [userconfigpath, configpath]
application = create_app(Production(configfiles), configfiles)

# see https://flask.palletsprojects.com/en/1.1.x/deploying/wsgi-standalone/#deploying-proxy-setups
from werkzeug.middleware.proxy_fix import ProxyFix
application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1, x_host=1)

