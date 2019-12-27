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
from .models import db, Role, User, Interest

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

    # initialize interests
    interests = [
        {'interest' : 'fsrc', 'description' : 'Frederick Steeplechasers Running Club', 'public' : True},
        {'interest' : 'l-and-h', 'description' : 'Lou and Harriet', 'public' : False},
    ]
    allinterests = []
    for interest in interests:
        thisinterest = Interest(**interest)
        db.session.add(thisinterest)
        db.session.flush()
        allinterests.append(thisinterest)


    # define owner if desired
    if defineowner:
        from flask import current_app
        rootuser = current_app.config['APP_OWNER']
        rootpw = current_app.config['APP_OWNER_PW']
        name = current_app.config['APP_OWNER_NAME']
        given_name = current_app.config['APP_OWNER_GIVEN_NAME']
        owner = User.query.filter_by(email=rootuser).first()
        if not owner:
            owner = user_datastore.create_user(email=rootuser, password=hash_password(rootpw), name=name, given_name=given_name)
            for rolename in allroles:
                user_datastore.add_role_to_user(owner, allroles[rolename])
        db.session.flush()
        owner = User.query.filter_by(email=rootuser).one()
        for thisinterest in allinterests:
            owner.interests.append(thisinterest)

    # and we're done, let's accept what we did
    db.session.commit()
