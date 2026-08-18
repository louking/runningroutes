'''
test_models - test runningroutes.models
=========================================================
'''

# pypi
import pytest

# homegrown
from runningroutes.models import db, priorityUpdater, getmodelitems, ModelItem, update_local_tables
from runningroutes.models import LocalUser, LocalInterest, Location
from loutilities.user.model import Interest, Application, User


# ----------------------------------------------------------------------
# priorityUpdater
# ----------------------------------------------------------------------

def test_priorityupdater_increments_from_initial():
    updater = priorityUpdater(10, 5)
    assert updater() == 10
    assert updater() == 15
    assert updater() == 20


def test_priorityupdater_independent_instances():
    a = priorityUpdater(0, 1)
    b = priorityUpdater(100, 10)
    assert a() == 0
    assert b() == 100
    assert a() == 1
    assert b() == 110


# ----------------------------------------------------------------------
# getmodelitems
# ----------------------------------------------------------------------

def test_getmodelitems_single_query_returns_single_item(bare_dbapp):
    loc = Location(location='here')
    db.session.add(loc)
    db.session.commit()

    getter = getmodelitems(Location, {'location': 'here'})
    assert getter() is loc


def test_getmodelitems_list_query_returns_list(bare_dbapp):
    loc1 = Location(location='here')
    loc2 = Location(location='there')
    db.session.add_all([loc1, loc2])
    db.session.commit()

    getter = getmodelitems(Location, [{'location': 'here'}, {'location': 'there'}])
    result = getter()
    assert result == [loc1, loc2]


def test_getmodelitems_resolves_callable_query_values(bare_dbapp):
    loc = Location(location='here')
    db.session.add(loc)
    db.session.commit()

    getter = getmodelitems(Location, {'location': lambda: 'here'})
    assert getter() is loc


# ----------------------------------------------------------------------
# ModelItem
# ----------------------------------------------------------------------

def test_modelitem_stores_attributes():
    item = ModelItem(Location, [{'location': 'here'}], cleartable=False, checkkeys=['location'])
    assert item.model is Location
    assert item.items == [{'location': 'here'}]
    assert item.cleartable is False
    assert item.checkkeys == ['location']


def test_modelitem_defaults():
    item = ModelItem(Location, [])
    assert item.cleartable is True
    assert item.checkkeys == []


# ----------------------------------------------------------------------
# update_local_tables
# ----------------------------------------------------------------------
# file-based sqlite (bare_dbapp, see conftest.py) is used throughout this suite rather than
# ':memory:', which sidesteps a :memory:-plus-cross-bind-query flush/commit visibility gotcha
# documented in the members repo's CLAUDE.md for this exact function

def test_update_local_tables_creates_localinterest_and_localuser(bare_dbapp):
    application = Application(application='routes')
    interest = Interest(interest='fsrc', description='FSRC', public=True)
    interest.applications.append(application)
    user = User(email='jane@example.com', name='Jane Doe', given_name='Jane', active=True,
                fs_uniquifier='uniq1')
    user.interests.append(interest)
    db.session.add_all([application, interest, user])
    db.session.commit()

    update_local_tables()

    linterest = LocalInterest.query.filter_by(interest_id=interest.id).one()
    luser = LocalUser.query.filter_by(user_id=user.id, interest_id=linterest.id).one()
    assert luser.email == 'jane@example.com'
    assert luser.active is True


def test_update_local_tables_ignores_interest_for_other_application(bare_dbapp):
    application = Application(application='routes')
    other_application = Application(application='members')
    interest = Interest(interest='other-app-interest', description='Not routes', public=True)
    interest.applications.append(other_application)
    db.session.add_all([application, other_application, interest])
    db.session.commit()

    update_local_tables()

    assert LocalInterest.query.filter_by(interest_id=interest.id).count() == 0


def test_update_local_tables_syncs_user_deactivation(bare_dbapp):
    application = Application(application='routes')
    interest = Interest(interest='fsrc', description='FSRC', public=True)
    interest.applications.append(application)
    user = User(email='jane@example.com', name='Jane Doe', given_name='Jane', active=True,
                fs_uniquifier='uniq1')
    user.interests.append(interest)
    db.session.add_all([application, interest, user])
    db.session.commit()
    update_local_tables()

    user.active = False
    db.session.commit()
    update_local_tables()

    linterest = LocalInterest.query.filter_by(interest_id=interest.id).one()
    luser = LocalUser.query.filter_by(user_id=user.id, interest_id=linterest.id).one()
    assert luser.active is False


def test_update_local_tables_passes_lockfile(monkeypatch):
    # regression test for louking/runningroutes#182: docker-compose.yml runs multiple
    # gunicorn workers, each independently calling update_local_tables() at boot. Without a
    # lockfile, ManageLocalTables.update() (loutilities.user.model) has no way to serialize
    # those workers, and concurrent callers can each insert their own duplicate localuser row
    # for a newly-synced (user_id, interest_id) -- see #180, #181. Confirm
    # update_local_tables() actually passes a lockfile through, rather than relying on
    # loutilities' default (unserialized) behavior.
    calls = {}

    class FakeManageLocalTables:
        def __init__(self, *args, **kwargs):
            calls['args'] = args
            calls['kwargs'] = kwargs

        def update(self):
            calls['updated'] = True

    monkeypatch.setattr('runningroutes.models.ManageLocalTables', FakeManageLocalTables)

    update_local_tables()

    assert calls['kwargs'].get('lockfile')
    assert calls['updated']
