'''
helpers - commonly needed utilities
====================================================================================
'''

# pypi
from flask import g
from loutilities.user.model import Interest

# homegrown
from .models import LocalInterest

def local2common_interest(linterest):
    """return Interest for a LocalInterest

    Args:
        localinterest (LocalInterest): LocalInterest instance

    Returns:
        Interest: Interest instance
    """
    return Interest.query.filter_by(id=linterest.interest_id).one()

def common2local_interest(cinterest):
    """return LocalInterest for an Interest

    Args:
        cinterest (Interest): Interest instance

    Returns:
        LocalInterest: LocalInterest instance
    """
    return LocalInterest.query.filter_by(interest_id=cinterest.id).one()

def localinterest():
    """return the currently selected LocalIntere

    Returns:
        LocalInterest: LocalInterest instance, or None if no interest selected
    """
    interest = Interest.query.filter_by(interest=g.interest).one_or_none()
    return LocalInterest.query.filter_by(interest_id=interest.id).one() if interest else None


