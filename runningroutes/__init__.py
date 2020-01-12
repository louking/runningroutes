###########################################################################################
# runningroutes - package
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/04/19        Lou King        Create
#
#   Copyright 2019 Lou King.  All rights reserved
###########################################################################################

# standard
import os.path

# pypi
from flask import Flask, send_from_directory, g, session, request, url_for
from flask_mail import Mail
from jinja2 import ChoiceLoader, PackageLoader
from flask_security import Security, SQLAlchemyUserDatastore, current_user

# homegrown
import loutilities
from loutilities.configparser import getitems
from runningroutes.models import Interest


# define security globals
user_datastore = None
security = None

# hold application here
app = None

# create application
def create_app(config_obj, config_filename=None):
    '''
    apply configuration object, then configuration filename
    '''
    global app
    app = Flask('runningroutes')
    app.config.from_object(config_obj)
    if config_filename:
        appconfig = getitems(config_filename, 'app')
        app.config.update(appconfig)

    # tell jinja to remove linebreaks
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # define product name (don't import nav until after app.jinja_env.globals['_productname'] set)
    app.jinja_env.globals['_productname'] = app.config['THISAPP_PRODUCTNAME']
    app.jinja_env.globals['_productname_text'] = app.config['THISAPP_PRODUCTNAME_TEXT']

    # initialize database
    from runningroutes.models import db
    db.init_app(app)

    # handle <interest> in URL - https://flask.palletsprojects.com/en/1.1.x/patterns/urlprocessors/
    @app.url_value_preprocessor
    def pull_interest(endpoint, values):
        try:
            g.interest = values.pop('interest', None)
        except AttributeError:
            g.interest = None
        finally:
            if not g.interest:
                g.interest = request.args.get('interest', None)

    # add loutilities tables-assets for js/css/template loading
    # see https://adambard.com/blog/fresh-flask-setup/
    #    and https://webassets.readthedocs.io/en/latest/environment.html#webassets.env.Environment.load_path
    # loutilities.__file__ is __init__.py file inside loutilities; os.path.split gets package directory
    loutilitiespath = os.path.join(os.path.split(loutilities.__file__)[0], 'tables-assets', 'static')

    @app.route('/loutilities/static/<path:filename>')
    def loutilities_static(filename):
        return send_from_directory(loutilitiespath, filename)

    # bring in js, css assets here, because app needs to be created first
    from .assets import asset_env, asset_bundles
    with app.app_context():
        # js/css files
        asset_env.append_path(app.static_folder)
        asset_env.append_path(loutilitiespath, '/loutilities/static')

        # templates
        loader = ChoiceLoader([
            app.jinja_loader,
            PackageLoader('loutilities', 'tables-assets/templates')
        ])
        app.jinja_loader = loader

    # initialize assets
    asset_env.init_app(app)
    asset_env.register(asset_bundles)

    # Set up Flask-Security
    from runningroutes.models import User, Role
    global user_datastore, security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    # Set up Flask-Mail [configuration in <application>.cfg
    mail = Mail(app)

    # activate views
    from runningroutes.views.frontend import bp as frontend
    app.register_blueprint(frontend)
    from runningroutes.views.admin import bp as admin
    app.register_blueprint(admin)

    # need to force app context else get
    #    RuntimeError: Working outside of application context.
    #    RuntimeError: Attempted to generate a URL without the application context being pushed.
    # see http://kronosapiens.github.io/blog/2014/08/14/understanding-contexts-in-flask.html
    with app.app_context():
        # import navigation after views created
        from runningroutes import nav

        # turn on logging
        from .applogging import setlogging
        setlogging()

        # set up scoped session
        from sqlalchemy.orm import scoped_session, sessionmaker
        db.session = scoped_session(sessionmaker(autocommit=False,
                                                 autoflush=False,
                                                 bind=db.engine))
        db.query = db.session.query_property()

        # handle favicon request for old browsers
        app.add_url_rule('/favicon.ico', endpoint='favicon',
                        redirect_to=url_for('static', filename='favicon.ico'))

    # ----------------------------------------------------------------------
    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            user = current_user
            email = user.email

            # used in layout.jinja2
            app.jinja_env.globals['user_interests'] = sorted([{'interest': i.interest, 'description': i.description}
                                                              for i in user.interests],
                                                             key=lambda a: a['description'].lower())
            session['user_email'] = email

        else:
            # used in layout.jinja2
            pubinterests = Interest.query.filter_by(public=True).all()
            app.jinja_env.globals['user_interests'] = sorted([{'interest': i.interest, 'description': i.description}
                                                              for i in pubinterests],
                                                             key=lambda a: a['description'].lower())
            session.pop('user_email', None)

    # ----------------------------------------------------------------------
    @app.after_request
    def after_request(response):
        if not app.config['DEBUG']:
            app.logger.info(
                '{}: {} {} {}'.format(request.remote_addr, request.method, request.url, response.status_code))
        return response

    # app back to caller
    return app




