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
def create_fidfile(group, filename, mimetype):
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