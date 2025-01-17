'''
applogging - define logging for the application
================================================
'''
# standard
from datetime import datetime

# pypi
from loutilities.timeu import asctime

# pick up common setlogging function (backwards compatibility)
from loutilities.user.applogging import setlogging


def timenow():
    """useful for logpoints"""
    return asctime('%H:%M:%S.%f').dt2asc(datetime.now())
