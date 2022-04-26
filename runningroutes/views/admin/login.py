###########################################################################################
# login - login and logout handling
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/13/19        Lou King        Create
#
#   Copyright 2019 Lou King.  All rights reserved
###########################################################################################

# standard
from operator import itemgetter

# pypi
from flask import request, session
from flask_login import user_logged_in, user_logged_out

# homegrown
from runningroutes import app

#----------------------------------------------------------------------
@user_logged_in.connect_via(app)
def do_login(sender, **kwargs):

    user = kwargs['user']
    email = user.email
    ip = request.remote_addr
    sender.logger.info('user log in {} from {}'.format(email, ip))

    # # used in layout.jinja2
    # moved to runningroutes.__init__.before_request
    # app.jinja_env.globals['user_interests'] = sorted([{'interest':i.interest, 'description':i.description}
    #                                                   for i in user.interests], key=lambda a: a['description'].lower())
    # session['user_email'] = email
    #
#----------------------------------------------------------------------
@user_logged_out.connect_via(app)
def do_logout(sender, **kwargs):

    user = kwargs['user']
    email = user.email
    ip = request.remote_addr
    sender.logger.info('user log out {} from {}'.format(email, ip))

    # # used in layout.jinja2
    # moved to runningroutes.__init__.before_request
    # app.jinja_env.globals['user_interests'] = []
    # session.pop('user_email', None)


