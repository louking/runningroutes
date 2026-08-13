'''
test_frontend - test runningroutes.views.frontend.frontend
=========================================================

views/frontend/frontend.py does `from runningroutes import app` at module import time (used by
UserRoute/UserTurns' legacy-redirect logging), so -- like locations.py (test_locations.py) and
nav.py (test_nav.py) -- it can only be imported once the `app` fixture's create_app() call has
already imported it as a side effect of registering the frontend blueprint. See the
frontend_module fixture below.
'''

# pypi
import pytest
from flask import g

# homegrown
from runningroutes.models import db, LocalInterest, Route, ROLE_SUPER_ADMIN, ROLE_ROUTES_ADMIN
from loutilities.user.model import Interest, Role

from fakecurrentuser import FakeCurrentUser


@pytest.fixture
def frontend_module(app):
    from runningroutes.views.frontend import frontend
    return frontend


@pytest.fixture
def roles(dbapp):
    superadmin = Role(name=ROLE_SUPER_ADMIN, description='super admin')
    routesadmin = Role(name=ROLE_ROUTES_ADMIN, description='routes admin')
    db.session.add_all([superadmin, routesadmin])
    db.session.commit()
    return {'super': superadmin, 'routes': routesadmin}


def _make_interest(slug, public):
    interest = Interest(interest=slug, description=slug, public=public)
    db.session.add(interest)
    db.session.commit()
    linterest = LocalInterest(interest_id=interest.id)
    db.session.add(linterest)
    db.session.commit()
    return interest, linterest


# ----------------------------------------------------------------------
# check_permission
# ----------------------------------------------------------------------

def test_check_permission_unknown_interest_false(dbapp, frontend_module, monkeypatch):
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))
    assert frontend_module.check_permission('no-such-interest') is False


def test_check_permission_anonymous_public_interest_true(dbapp, frontend_module, monkeypatch):
    interest, _ = _make_interest('fsrc', public=True)
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))
    assert frontend_module.check_permission('fsrc') is True


def test_check_permission_anonymous_private_interest_false(dbapp, frontend_module, monkeypatch):
    _make_interest('private-club', public=False)
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))
    assert frontend_module.check_permission('private-club') is False


def test_check_permission_authenticated_public_interest_true(dbapp, frontend_module, monkeypatch):
    interest, _ = _make_interest('fsrc', public=True)
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=True))
    assert frontend_module.check_permission('fsrc') is True


def test_check_permission_authenticated_private_no_roles_false(roles, frontend_module, monkeypatch):
    _make_interest('private-club', public=False)
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(roles=[], is_authenticated=True))
    assert frontend_module.check_permission('private-club') is False


def test_check_permission_authenticated_private_superadmin_true(roles, frontend_module, monkeypatch):
    _make_interest('private-club', public=False)
    monkeypatch.setattr(frontend_module, 'current_user',
                         FakeCurrentUser(roles=[roles['super']], is_authenticated=True))
    assert frontend_module.check_permission('private-club') is True


def test_check_permission_authenticated_routesadmin_with_interest_true(roles, frontend_module, monkeypatch):
    interest, _ = _make_interest('private-club', public=False)
    monkeypatch.setattr(frontend_module, 'current_user',
                         FakeCurrentUser(roles=[roles['routes']], interests=[interest], is_authenticated=True))
    assert frontend_module.check_permission('private-club') is True


def test_check_permission_authenticated_routesadmin_without_interest_false(roles, frontend_module, monkeypatch):
    _make_interest('private-club', public=False)
    monkeypatch.setattr(frontend_module, 'current_user',
                         FakeCurrentUser(roles=[roles['routes']], interests=[], is_authenticated=True))
    assert frontend_module.check_permission('private-club') is False


# ----------------------------------------------------------------------
# UserRoutes
# ----------------------------------------------------------------------

def test_userroutes_permission_delegates_to_check_permission(dbapp, frontend_module, monkeypatch, app):
    interest, _ = _make_interest('fsrc', public=True)
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))

    with app.test_request_context():
        g.interest = 'fsrc'
        assert frontend_module.UserRoutes().permission() is True


def test_userroutes_beforequery_sets_interest_id(dbapp, frontend_module, app):
    interest, linterest = _make_interest('fsrc', public=True)

    with app.test_request_context():
        g.interest = 'fsrc'
        view = frontend_module.UserRoutes()
        view.beforequery()
        assert view.queryparams == {'interest_id': linterest.id}


def test_userroutes_beforequery_unknown_interest_uses_zero(dbapp, frontend_module, app):
    with app.test_request_context():
        g.interest = 'no-such-interest'
        view = frontend_module.UserRoutes()
        view.beforequery()
        assert view.queryparams == {'interest_id': 0}


def test_userroutes_retrieverows_skips_inactive_and_sorts_by_name(dbapp, frontend_module, app):
    interest, linterest = _make_interest('fsrc', public=True)
    db.session.add_all([
        Route(interest_id=linterest.id, name='Zebra Loop', latlng='39.1,-77.1', active=True,
              distance=3.0, surface='road', elevation_gain=100, description='d', gpx_file_id='g1'),
        Route(interest_id=linterest.id, name='Apple Loop', latlng='39.2,-77.2', active=True,
              distance=4.0, surface='trail', elevation_gain=50, description='d', gpx_file_id='g2'),
        Route(interest_id=linterest.id, name='Inactive Loop', latlng='39.3,-77.3', active=False,
              distance=5.0, surface='road', elevation_gain=10, description='d', gpx_file_id='g3'),
    ])
    db.session.commit()

    with app.test_request_context():
        view = frontend_module.UserRoutes()
        view.queryparams = {'interest_id': linterest.id}
        resp = view._retrieverows()
        geo = resp.get_json()

    names = [f['geometry']['properties']['name'] for f in geo['features']]
    assert names == ['Apple Loop', 'Zebra Loop']


# ----------------------------------------------------------------------
# UserRoute / UserTurns permission
# ----------------------------------------------------------------------

def test_userroute_permission_checks_routes_interest(dbapp, frontend_module, monkeypatch, app):
    interest, linterest = _make_interest('fsrc', public=True)
    route = Route(interest_id=linterest.id, name='Loop', latlng='39.1,-77.1', active=True)
    db.session.add(route)
    db.session.commit()
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))

    with app.test_request_context():
        assert frontend_module.UserRoute().permission(route.id) is True


def test_userturns_retrieverows_splits_turns_on_newline(dbapp, frontend_module, monkeypatch, app):
    interest, linterest = _make_interest('fsrc', public=True)
    route = Route(interest_id=linterest.id, name='Loop', latlng='39.1,-77.1', active=True,
                   turns='turn 1\nturn 2\nturn 3')
    db.session.add(route)
    db.session.commit()
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))

    with app.test_request_context():
        resp = frontend_module.UserTurns()._retrieverows(route.id)
        data = resp.get_json()

    assert data == {'status': 'success', 'turns': ['turn 1', 'turn 2', 'turn 3']}


def test_userturns_retrieverows_no_turns_returns_empty_list(dbapp, frontend_module, monkeypatch, app):
    interest, linterest = _make_interest('fsrc', public=True)
    route = Route(interest_id=linterest.id, name='Loop', latlng='39.1,-77.1', active=True, turns=None)
    db.session.add(route)
    db.session.commit()
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))

    with app.test_request_context():
        resp = frontend_module.UserTurns()._retrieverows(route.id)
        data = resp.get_json()

    assert data == {'status': 'success', 'turns': []}
