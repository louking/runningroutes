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
from os import remove

# pypi
from flask import current_app
from loutilities.tables import DbCrudApiRolePermissions

# homegrown
from . import bp
from ...models import db, Files, Interest
from ...version import __docversion__

adminguide = f'https://runningroutes.readthedocs.io/en/{__docversion__}/admin-guide.html'

###########################################################################################
# files endpoint
###########################################################################################

class FilesCrud(DbCrudApiRolePermissions):
    # ----------------------------------------------------------------------
    def deleterow(self, thisid):
        '''
        deletes row in Files, and deletes the file itself

        :param thisid: id of row to be deleted
        :return: []
        '''

        # determine the path of the file to delete. Note self.model = Files
        file = self.model.query.filter_by(id=thisid).one()
        fid = file.fileid
        mainfolder = current_app.config['APP_FILE_FOLDER']
        groupfolder = join(mainfolder, file.interest.interest)
        filepath = join(groupfolder, fid)

        # delete the Files record -- return what the super returns ([])
        row = super(FilesCrud, self).deleterow(thisid)

        # delete the file
        if exists(filepath):
            remove(filepath)

        return row

files_dbattrs = 'id,fileid,filename,route_id,interest,mimetype'.split(',')
files_formfields = 'rowid,fileid,filename,route_id,interest,mimetype'.split(',')
files_dbmapping = dict(zip(files_dbattrs, files_formfields))
files_formmapping = dict(zip(files_formfields, files_dbattrs))

files = FilesCrud(
                    app = bp,   # use blueprint instead of app
                    db = db,
                    model = Files,
                    roles_accepted = 'super-admin',
                    template = 'datatables.jinja2',
                    templateargs={'adminguide': adminguide},
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

