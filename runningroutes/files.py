###########################################################################################
# files - file administration
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/30/19        Lou King        Create
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
from .models import db, Files, Interest

# ----------------------------------------------------------------------
def create_fidfile(group, filename, mimetype, fid=None):
    '''
    create directory structure for file group
    create a file in the database which has a fileid
    determine pathname for file

    NOTE: while directory structure is created here and filepath is determined, caller must save file

    :param group: files are grouped by "group", to allow separate permissions for separate groups
    :param filename: name of file
    :param mimetype: mimetype for file
    :param fid: optional file id, only used for initial data load
    :return: fid, filepath
    '''

    # make folder(s) if not there already
    mainfolder = current_app.config['APP_FILE_FOLDER']
    if not exists(mainfolder):
        # ug+rwx
        # note not getting g+w, issue #63
        mkdir(mainfolder, mode=0o770)
    groupfolder = join(mainfolder, group)
    if not exists(groupfolder):
        mkdir(groupfolder, mode=0o770)

    # create file and save it's record; uuid4 gives unique fileid
    filename = filename
    # fid might be specified by caller -- this is only for external data loading
    if not fid:
        fid = uuid4().hex
    filepath = join(groupfolder, fid)
    # TODO: how can the next two lines be made generic?
    interest = Interest.query.filter_by(interest=group).one()
    file = Files(fileid=fid, filename=filename, interest=interest, mimetype=mimetype)
    db.session.add(file)
    db.session.commit()  # file is fully stored now

    return fid, filepath

# ----------------------------------------------------------------------
def get_fidfile(fid):
    file = Files.query.filter_by(fileid=fid).one()
    mainfolder = current_app.config['APP_FILE_FOLDER']
    # TODO: how can the next line be made generic?
    groupfolder = join(mainfolder, file.interest.interest)
    filepath = join(groupfolder, fid)

    # this assumes text file
    with open(filepath, 'r') as f:
        contents = f.readlines()

    return {'group':file.interest, 'contents':contents}