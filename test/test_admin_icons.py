'''
test_admin_icons - test runningroutes.views.admin.icons

views/admin/icons.py builds `gmaps` from `app.config[...]` at *module import time* (from ... import
app) -- see test_admin_routes.py for the same pattern and why the admin_icons_module fixture below
defers the import until after the `app` fixture has run.

Like test_admin_routes.py, these tests call the IconsCrud/IconLocationCrud overrides that don't
themselves render_template() directly on the module-level singletons (icon, iconmap) rather than
exercising the full DataTables server-side protocol.
'''

# pypi
import pytest
from flask import g, request
from loutilities.tables import get_request_action, get_request_data

# homegrown
from runningroutes.models import (
    db, LocalInterest, Route, Files, Location, IconMap, ROLE_SUPER_ADMIN, ROLE_ICON_ADMIN,
    ICON_FILE_ROUTE,
)
from loutilities.user.model import Interest, Role

from fakecurrentuser import FakeCurrentUser


@pytest.fixture
def admin_icons_module(app):
    from runningroutes.views.admin import icons
    return icons


@pytest.fixture
def roles(dbapp):
    superadmin = Role(name=ROLE_SUPER_ADMIN, description='super admin')
    iconadmin = Role(name=ROLE_ICON_ADMIN, description='icon admin')
    db.session.add_all([superadmin, iconadmin])
    db.session.commit()
    return {'super': superadmin, 'icon': iconadmin}


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
# IconsCrud.permission
# ----------------------------------------------------------------------

def test_permission_denied_when_not_authenticated(dbapp, admin_icons_module, monkeypatch, app):
    monkeypatch.setattr(admin_icons_module, 'current_user', FakeCurrentUser(is_authenticated=False))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_icons_module.icon.permission() is False


def test_permission_denied_when_no_interest(dbapp, admin_icons_module, monkeypatch, app):
    monkeypatch.setattr(admin_icons_module, 'current_user', FakeCurrentUser(is_authenticated=True))
    with app.test_request_context():
        g.interest = 'no-such-interest'
        assert admin_icons_module.icon.permission() is False


def test_permission_granted_for_superadmin(interestsetup, admin_icons_module, monkeypatch, app):
    monkeypatch.setattr(admin_icons_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['super']], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_icons_module.icon.permission() is True


def test_permission_denied_for_non_admin_role(interestsetup, admin_icons_module, monkeypatch, app):
    monkeypatch.setattr(admin_icons_module, 'current_user', FakeCurrentUser(roles=[], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_icons_module.icon.permission() is False


def test_permission_granted_for_iconadmin_with_interest(interestsetup, admin_icons_module, monkeypatch, app):
    monkeypatch.setattr(admin_icons_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['icon']], interests=[interestsetup['interest']],
                                          is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_icons_module.icon.permission() is True


def test_permission_denied_for_iconadmin_without_interest(interestsetup, admin_icons_module, monkeypatch, app):
    monkeypatch.setattr(admin_icons_module, 'current_user',
                         FakeCurrentUser(roles=[interestsetup['icon']], interests=[], is_authenticated=True))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert admin_icons_module.icon.permission() is False


# ----------------------------------------------------------------------
# IconsCrud.beforequery
# ----------------------------------------------------------------------

def test_beforequery_sets_interest_id(interestsetup, admin_icons_module, app):
    with app.test_request_context():
        g.interest = 'fsrc'
        icon = admin_icons_module.icon
        icon.beforequery()
        assert icon.queryparams['interest_id'] == interestsetup['linterest'].id


# ----------------------------------------------------------------------
# IconsCrud.set_files_icon
# ----------------------------------------------------------------------

def test_set_files_icon_points_files_at_fake_icon_route(interestsetup, admin_icons_module, app):
    linterest = interestsetup['linterest']
    fakeroute = Route(name=ICON_FILE_ROUTE, description='fake route')
    svg_file = Files(interest_id=linterest.id, fileid='svg1', filename='marker.svg')
    db.session.add_all([fakeroute, svg_file])
    db.session.commit()

    admin_icons_module.icon.set_files_icon(['svg1'])
    db.session.commit()

    assert Files.query.filter_by(fileid='svg1').one().route_id == fakeroute.id


# ----------------------------------------------------------------------
# IconLocationCrud.editor_method_posthook
# ----------------------------------------------------------------------

def _form(app, action, thisid, **fields):
    data = {'action': action}
    for field, value in fields.items():
        data['data[{}][{}]'.format(thisid, field)] = value
    return app.test_request_context('/', method='POST', data=data)


def test_editor_method_posthook_ignores_remove_action(interestsetup, admin_icons_module, app):
    iconmap = IconMap(interest_id=interestsetup['linterest'].id, page_title='Map')
    db.session.add(iconmap)
    db.session.commit()

    with _form(app, 'remove', iconmap.id, location='ignored'):
        admin_icons_module.iconmap._responsedata = [{}]
        admin_icons_module.iconmap.editor_method_posthook(request.form)

    assert IconMap.query.filter_by(id=iconmap.id).one().location_id is None


def test_editor_method_posthook_create_assigns_new_location(interestsetup, admin_icons_module, app, monkeypatch):
    iconmap = IconMap(interest_id=interestsetup['linterest'].id, page_title='Map')
    db.session.add(iconmap)
    db.session.commit()

    newloc = Location(location='123 Main St')
    db.session.add(newloc)
    db.session.commit()
    monkeypatch.setattr(admin_icons_module.gmaps, 'get_location',
                         lambda location, loc_id, cache_limit: {'id': newloc.id, 'coordinates': [1, 2]})

    view = admin_icons_module.iconmap
    view.created_id = iconmap.id
    view._responsedata = [{}]

    with _form(app, 'create', iconmap.id, location='123 Main St'):
        view.editor_method_posthook(request.form)

    updated = IconMap.query.filter_by(id=iconmap.id).one()
    assert updated.location_id == newloc.id
    assert view._responsedata[0]['location'] == '123 Main St'


def test_editor_method_posthook_edit_changed_location_replaces_record(
        interestsetup, admin_icons_module, app, monkeypatch):
    oldloc = Location(location='Old Address')
    db.session.add(oldloc)
    db.session.commit()
    iconmap = IconMap(interest_id=interestsetup['linterest'].id, page_title='Map', location_id=oldloc.id)
    db.session.add(iconmap)
    db.session.commit()
    oldloc_id = oldloc.id

    newloc = Location(location='New Address')
    db.session.add(newloc)
    db.session.commit()

    calls = []
    def fake_get_location(location, loc_id, cache_limit):
        calls.append(loc_id)
        return {'id': newloc.id, 'coordinates': [1, 2]}
    monkeypatch.setattr(admin_icons_module.gmaps, 'get_location', fake_get_location)

    view = admin_icons_module.iconmap
    view._responsedata = [{}]

    with _form(app, 'edit', iconmap.id, location='New Address'):
        view.editor_method_posthook(request.form)
    # db.session is built with autoflush=False (runningroutes/__init__.py) -- production commits
    # after editor_method_posthook() as part of the DataTables editor flow; mirror that here so
    # the pending delete is actually visible to the query below
    db.session.commit()

    assert calls == [None]  # old location record was deleted, so no loc_id passed through for reuse
    assert Location.query.filter_by(id=oldloc_id).one_or_none() is None
    assert IconMap.query.filter_by(id=iconmap.id).one().location_id == newloc.id


def test_editor_method_posthook_edit_unchanged_location_keeps_record(
        interestsetup, admin_icons_module, app, monkeypatch):
    loc = Location(location='Same Address')
    db.session.add(loc)
    db.session.commit()
    iconmap = IconMap(interest_id=interestsetup['linterest'].id, page_title='Map', location_id=loc.id)
    db.session.add(iconmap)
    db.session.commit()

    calls = []
    def fake_get_location(location, loc_id, cache_limit):
        calls.append(loc_id)
        return {'id': loc.id, 'coordinates': [1, 2]}
    monkeypatch.setattr(admin_icons_module.gmaps, 'get_location', fake_get_location)

    view = admin_icons_module.iconmap
    view._responsedata = [{}]

    with _form(app, 'edit', iconmap.id, location='Same Address'):
        view.editor_method_posthook(request.form)

    assert calls == [loc.id]  # unchanged location's id was passed through for cache reuse
    assert Location.query.filter_by(id=loc.id).one_or_none() is not None
