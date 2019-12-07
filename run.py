###########################################################################################
# run - run the web application for development
#
#       Date            Author          Reason
#       ----            ------          ------
#       11/07/19        Lou King        Create
#
#   Copyright 2019 Lou King
###########################################################################################

'''
use this script to run the web application

Usage::

    python run.py
'''

# standard
import sys
import os.path

# homegrown
from runningroutes import create_app
from runningroutes.settings import Development


configfile = "runningroutes.cfg"
abspath = os.path.abspath(__file__)
configpath = os.path.join(os.path.dirname(abspath), 'config', configfile)
app = create_app(Development(configpath), configpath)

from loutilities.flask_helpers.blueprints import list_routes

debug = True

if debug:
    with app.app_context():
        pass
        print('listing routes from run.py')
        list_routes(app)

if __name__ == "__main__":
    if "--setup" in sys.argv:
        with app.app_context():
            # must be within app context
            from runningroutes.models import db
            db.create_all()
            db.session.commit()
            print("Database tables created")

    elif "--RESET" in sys.argv:
        with app.app_context():
            # must be within app context
            from runningroutes.models import db
            from runningroutes.dbinit import init_db
            db.drop_all()
            db.create_all()

            # initialize database
            init_db()

            db.session.commit()
            print("Database tables reset")

    else:
        # see http://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html
        import os
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        app.run(debug=True)