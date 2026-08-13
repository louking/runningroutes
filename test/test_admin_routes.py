'''
test_admin_routes - test runningroutes.views.admin.routes

views/admin/routes.py builds `gmapsclient`/`gmaps`/`geodist` from `app.config[...]` at *module
import time* (from . import app), so -- like locations.py/nav.py/frontend.py -- it can only be
imported once the `app` fixture's create_app() call has already imported it as a side effect of
registering the admin blueprint. See the admin_routes_module fixture below.

Rather than exercising the full DataTables server-side request/response protocol (which needs a
live route -- see the members repo's CLAUDE.md for why its DbCrudApiInterestsRolePermissions-based
views were excluded on that basis), these tests call the RunningRoutesTable overrides that don't
themselves render_template() directly on the module-level `rrtable` singleton: permission(),
beforequery(), snaploc(), and set_files_route().
'''

# pypi
import pytest
from flask import g

# homegrown
from runningroutes.models import db, LocalInterest, Route, Files, ROLE_SUPER_ADMIN, ROLE_ROUTES_ADMIN
from loutilities.user.model import Interest, Role

from fakecurrentuser import FakeCurrentUser


@pytest.fixture
def admin_routes_module(app):
    from runningroutes.views.admin import routes
    return routes


@pytest.fixture
def roles(dbapp):
    superadmin = Role(name=ROLE_SUPER_ADMIN, description='super admin')
    routesadmin = Role(name=ROLE_ROUTES_ADMIN, description='routes admin')
    db.session.add_all([superadmin, routesadmin])
    db.session.commit()
    return {'super': superadmin, 'routes': routesadmin}


@pytest.fixture
def interestsetup(roles):
    interest = Interest(interest='fsrc', description='FSRC')
    db.session.add(interest)
    db.session.commit()
    linterest = LocalInterest(interest_id=interest.id)
    db.session.add(linterest)
    db.session.commit()
    return {'interest': interest, 'linterest': linterest, **roles}


# ----------------------------------------------------------------------
# permission
# ----------------------------------------------------------------------

def test_permission_denied_when_not_authenticated(dbapp, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user', FakeCurrentUser(is_authenticated=False))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_routes_module.rrtable.permission() is False


def test_permission_denied_when_no_interest(dbapp, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user', FakeCurrentUser(is_authenticated=True))
    with app.test_request_context():
        g.interest = 'no-such-interest'
        assert admin_routes_module.rrtable.permission() is False


def test_permission_granted_for_superadmin(interestsetup, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['super']], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_routes_module.rrtable.permission() is True


def test_permission_denied_for_non_admin_role(interestsetup, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user',
                         FakeCurrentUser(roles=[], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_routes_module.rrtable.permission() is False


def test_permission_granted_for_routesadmin_with_interest(interestsetup, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['routes']], interests=[interestsetup['interest']],
                                          is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_routes_module.rrtable.permission() is True


def test_permission_denied_for_routesadmin_without_interest(interestsetup, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['routes']], interests=[], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_routes_module.rrtable.permission() is False


# ----------------------------------------------------------------------
# beforequery
# ----------------------------------------------------------------------

def test_beforequery_sets_interest_id_from_permission(interestsetup, admin_routes_module, monkeypatch, app):
    monkeypatch.setattr(admin_routes_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['super']], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        rrtable = admin_routes_module.rrtable
        assert rrtable.permission() is True
        rrtable.beforequery()
        assert rrtable.queryparams['interest_id'] == interestsetup['linterest'].id


# ----------------------------------------------------------------------
# set_files_route
# ----------------------------------------------------------------------

def test_set_files_route_points_listed_files_at_route_and_clears_others(
        interestsetup, admin_routes_module, app):
    linterest = interestsetup['linterest']
    route = Route(interest_id=linterest.id, name='Loop', latlng='39.1,-77.1', active=True)
    other_route = Route(interest_id=linterest.id, name='Other', latlng='39.2,-77.2', active=True)
    db.session.add_all([route, other_route])
    db.session.commit()

    stale_file = Files(interest_id=linterest.id, route_id=route.id, fileid='stale', filename='old.gpx')
    keep_file = Files(interest_id=linterest.id, fileid='keep', filename='new.gpx')
    db.session.add_all([stale_file, keep_file])
    db.session.commit()

    # dbapp (via interestsetup/roles) already pushed an app context for this test -- nesting
    # another app_context() here would trigger Flask-SQLAlchemy's teardown_appcontext session
    # removal on exit, detaching `route` before the asserts below can use it
    admin_routes_module.rrtable.set_files_route(route.id, ['keep'])
    db.session.commit()

    assert Files.query.filter_by(fileid='stale').one().route_id is None
    assert Files.query.filter_by(fileid='keep').one().route_id == route.id


# ----------------------------------------------------------------------
# snaploc
# ----------------------------------------------------------------------

def test_snaploc_keeps_new_location_when_no_nearby_routes(interestsetup, admin_routes_module):
    rrtable = admin_routes_module.rrtable
    rrtable.queryparams = {'interest_id': interestsetup['linterest'].id}
    result = rrtable.snaploc('39.414300, -77.410300')

    assert result == '39.414300,-77.410300'


def test_snaploc_snaps_to_existing_close_route(interestsetup, admin_routes_module):
    linterest = interestsetup['linterest']
    existing = Route(interest_id=linterest.id, name='Existing', latlng='39.414300,-77.410300', active=True)
    db.session.add(existing)
    db.session.commit()

    rrtable = admin_routes_module.rrtable
    rrtable.queryparams = {'interest_id': linterest.id}
    # a few meters away -- well within APP_ROUTE_LOC_EPSILON (20m, Testing config)
    result = rrtable.snaploc('39.414310, -77.410310')

    assert result == '39.414300,-77.410300'


def test_snaploc_geocodes_address_string(interestsetup, admin_routes_module, monkeypatch):
    monkeypatch.setattr(admin_routes_module.gmaps.gmapsclient, 'geocode',
                         lambda address: [{'geometry': {'location': {'lat': 39.4143, 'lng': -77.4103}}}])

    rrtable = admin_routes_module.rrtable
    rrtable.queryparams = {'interest_id': interestsetup['linterest'].id}
    result = rrtable.snaploc('123 Main St, Frederick, MD')

    assert result == '39.414300,-77.410300'
