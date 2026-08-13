'''
test_helpers - test runningroutes.helpers
=========================================================
'''

# pypi
from flask import g

# homegrown
from runningroutes.helpers import local2common_interest, common2local_interest, localinterest
from runningroutes.models import db, LocalInterest
from loutilities.user.model import Interest


def _make_interest_pair(interest_slug='fsrc'):
    interest = Interest(interest=interest_slug, description='FSRC')
    db.session.add(interest)
    db.session.commit()
    linterest = LocalInterest(interest_id=interest.id)
    db.session.add(linterest)
    db.session.commit()
    return interest, linterest


def test_local2common_interest_returns_matching_interest(bare_dbapp):
    interest, linterest = _make_interest_pair()

    assert local2common_interest(linterest).id == interest.id


def test_common2local_interest_returns_matching_localinterest(bare_dbapp):
    interest, linterest = _make_interest_pair()

    assert common2local_interest(interest).id == linterest.id


def test_localinterest_returns_localinterest_for_g_interest(bare_dbapp):
    interest, linterest = _make_interest_pair()

    with bare_dbapp.test_request_context():
        g.interest = interest.interest
        assert localinterest().id == linterest.id


def test_localinterest_returns_none_when_g_interest_unknown(bare_dbapp):
    with bare_dbapp.test_request_context():
        g.interest = 'no-such-interest'
        assert localinterest() is None
