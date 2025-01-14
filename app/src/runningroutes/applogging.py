#!/usr/bin/python
###########################################################################################
# applogging - define logging for the application
#
#   Date        Author          Reason
#   ----        ------          ------
#   07/06/18    Lou King        Create (from https://github.com/louking/rrwebapp/blob/master/rrwebapp/applogging.py)
#
#   Copyright 2018 Lou King
#
###########################################################################################
'''
applogging - define logging for the application
================================================
'''
# standard
import logging
from logging.handlers import SMTPHandler
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler
from flask import current_app


# pypi

# homegrown

# ----------------------------------------------------------------------
def setlogging():
    # ----------------------------------------------------------------------

    # this is needed for any INFO or DEBUG logging
    current_app.logger.setLevel(logging.DEBUG)

    # # patch werkzeug logging -- not sure why this is being bypassed in werkzeug._internal._log
    # *** for some reason the following code caued debug pin not to be shown, see https://github.com/louking/rrwebapp/issues/300
    # werkzeug_logger = logging.getLogger('werkzeug')
    # werkzeug_logger.setLevel(logging.INFO)

    # TODO: move this to new module logging, bring in from dispatcher
    # set up logging
    ADMINS = ['lou.king@steeplechasers.org']
    if not current_app.debug:
        mail_handler = SMTPHandler('localhost',
                                   'noreply@steeplechasers.org',
                                   ADMINS, 'routes exception encountered')
        if 'LOGGING_LEVEL_MAIL' in current_app.config:
            mailloglevel = current_app.config['LOGGING_LEVEL_MAIL']
        else:
            mailloglevel = logging.ERROR
        mail_handler.setLevel(mailloglevel)
        mail_handler.setFormatter(Formatter('''
        Message type:       %(levelname)s
        Location:           %(pathname)s:%(lineno)d
        Module:             %(module)s
        Function:           %(funcName)s
        Time:               %(asctime)s

        Message:

        %(message)s
        '''))
        current_app.logger.addHandler(mail_handler)
        current_app.config['LOGGING_MAIL_HANDLER'] = mail_handler

        logpath = None
        if 'LOGGING_PATH' in current_app.config:
            logpath = current_app.config['LOGGING_PATH']

        if logpath:
            # file rotates every Monday
            file_handler = TimedRotatingFileHandler(logpath, when='W0', delay=True)
            if 'LOGGING_LEVEL_FILE' in current_app.config:
                fileloglevel = current_app.config['LOGGING_LEVEL_FILE']
            else:
                fileloglevel = logging.WARNING
            file_handler.setLevel(fileloglevel)
            current_app.logger.addHandler(file_handler)
            current_app.config['LOGGING_FILE_HANDLER'] = file_handler

            file_handler.setFormatter(Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))


