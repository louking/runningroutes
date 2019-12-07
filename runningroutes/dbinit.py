###########################################################################################
# dbinit - contracts database initialization
#
#       Date            Author          Reason
#       ----            ------          ------
#       10/18/18        Lou King        Create
#
#   Copyright 2018 Lou King
###########################################################################################
'''
dbinit - contracts database initialization
==================================================
'''

# homegrown
from .models import db, Role, User

#--------------------------------------------------------------------------
def init_db(defineowner=True):
#--------------------------------------------------------------------------
    # init the modelitems from dbinit_contracts

    # must wait until user_datastore is initialized before import
    from runningroutes import user_datastore
    from flask_security import hash_password

    # special processing for user roles because need to remember the roles when defining the owner
    # define user roles here
    userroles = [
        {'name':'super-admin',    'description':'everything'},
        {'name':'interest-admin', 'description':'interest administrator'},
    ]

    # initialize roles, remembering what roles we have    
    allroles = {}
    for userrole in userroles:
        rolename = userrole['name']
        allroles[rolename] = Role.query.filter_by(name=rolename).first() or user_datastore.create_role(**userrole)
    
    # define owner if desired
    if defineowner:
        from flask import current_app
        rootuser = current_app.config['APP_OWNER']
        rootpw = current_app.config['APP_OWNER_PW']
        owner = User.query.filter_by(email=rootuser).first()
        if not owner:
            owner = user_datastore.create_user(email=rootuser, password=hash_password(rootpw))
            for rolename in allroles:
                user_datastore.add_role_to_user(owner, allroles[rolename])

    # and we're done, let's accept what we did
    db.session.commit()
