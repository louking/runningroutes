###########################################################################################
# files - file administration
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/24/19        Lou King        Create
#
#   Copyright 2019 Lou King.  All rights reserved
###########################################################################################

# standard
from os.path import join, exists
from os import mkdir
from uuid import uuid4

# pypi
from flask import current_app

# homegrown
from . import bp
from runningroutes.models import db, Files, Interest
from loutilities.tables import DbCrudApiRolePermissions

# ----------------------------------------------------------------------
def create_fidfile(group, filename):
    # make folder(s) if not there already
    mainfolder = current_app.config['APP_FILE_FOLDER']
    if not exists(mainfolder):
        # ug:rw
        mkdir(mainfolder, mode=0o660)
    groupfolder = join(mainfolder, group)
    if not exists(groupfolder):
        mkdir(groupfolder, mode=0o660)

    # create file and save it's record; uuid4 gives unique fileid
    filename = filename
    fid = uuid4().hex
    filepath = join(groupfolder, fid)
    # TODO: how can the next two lines be made generic?
    interest = Interest.query.filter_by(interest=group).one()
    file = Files(fileid=fid, filename=filename, interest=interest)
    db.session.add(file)
    db.session.commit()  # file is fully stored now

    return fid, filepath

###########################################################################################
# files endpoint
###########################################################################################

files_dbattrs = 'id,fileid,filename,route_id,interest'.split(',')
files_formfields = 'rowid,fileid,filename,route_id,interest'.split(',')
files_dbmapping = dict(zip(files_dbattrs, files_formfields))
files_formmapping = dict(zip(files_formfields, files_dbattrs))

files = DbCrudApiRolePermissions(
                    app = bp,   # use blueprint instead of app
                    db = db,
                    model = Files,
                    files_accepted = 'super-admin',
                    template = 'datatables.jinja2',
                    pagename = 'files', 
                    endpoint = 'admin.files', 
                    rule = '/files',
                    dbmapping = files_dbmapping,
                    formmapping = files_formmapping,
                    clientcolumns = [
                        { 'data': 'filename', 'name': 'filename', 'label': 'Filename',
                          'className': 'field_req',
                          },
                        { 'data': 'fileid', 'name': 'fileid', 'label': 'File Id', '_unique': True,
                          'className': 'field_req',
                          },
                        { 'data': 'route_id', 'name': 'route_id', 'label': 'Route ID',
                        },
                        {'data': 'interest', 'name': 'interest', 'label': 'Interest',
                         '_treatment': {'relationship': {'fieldmodel': Interest, 'labelfield': 'description',
                                                         'formfield': 'interest', 'dbfield': 'interest',
                                                         'uselist': False, }
                                        }},
                    ],
                    servercolumns = None,  # not server side
                    idSrc = 'rowid', 
                    buttons = ['remove'],
                    dtoptions = {
                                        'scrollCollapse': True,
                                        'scrollX': True,
                                        'scrollXInner': "100%",
                                        'scrollY': True,
                                  },
                    )
files.register()

