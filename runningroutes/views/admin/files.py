###########################################################################################
# files - file administration
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/24/19        Lou King        Create
#
#   Copyright 2019 Lou King.  All rights reserved
###########################################################################################

# homegrown
from . import bp
from runningroutes.models import db, Files, Interest
from loutilities.tables import DbCrudApiRolePermissions

###########################################################################################
# files endpoint
###########################################################################################

files_dbattrs = 'id,fileid,filename,route_id,interest,mimetype'.split(',')
files_formfields = 'rowid,fileid,filename,route_id,interest,mimetype'.split(',')
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
                          },
                        { 'data': 'mimetype', 'name': 'mimetype', 'label': 'MIME type',
                          },
                        { 'data': 'fileid', 'name': 'fileid', 'label': 'File Id', '_unique': True,
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

