'''
test_nav - test runningroutes.nav
=========================================================

runningroutes.nav does two things at *module import time* that this file has to work around:
  - the collections.MutableMapping monkeypatch flask_nav needs on Python 3.10+ (see nav.py's
    top-of-file comment / this repo's CLAUDE.md "Known Quirks") -- applied here too, before
    flask_nav.elements is imported, in case something else imports flask_nav first
  - `thisnav.init_app(current_app)`, which needs a real active app context -- so runningroutes.nav
    itself can only be imported once the `app` fixture's create_app() call has already imported it
    (create_app() does so inside its own `with app.app_context():` block); see the nav_module
    fixture below, and test_locations.py for the same pattern applied to locations.py
'''

# standard
import collections
collections.MutableMapping = collections.abc.MutableMapping

# pypi
import pytest
from flask import g
from flask_nav.elements import View, Subgroup

# homegrown
from runningroutes.models import ROLE_SUPER_ADMIN, ROLE_ROUTES_ADMIN, ROLE_ICON_ADMIN

from fakecurrentuser import FakeCurrentUser


@pytest.fixture
def nav_module(app):
    from runningroutes import nav
    return nav


def _menu(app, nav_module, monkeypatch, roles=(), interest='fsrc', is_authenticated=True):
    monkeypatch.setattr(nav_module, 'current_user', FakeCurrentUser(roles=roles, is_authenticated=is_authenticated))
    with app.test_request_context():
        g.interest = interest
        return nav_module.nav_menu()


def _endpoints(navbar):
    return [item.endpoint for item in navbar.items if isinstance(item, View)]


def _subgroup(navbar, title):
    for item in navbar.items:
        if isinstance(item, Subgroup) and item.title == title:
            return item
    return None


def test_nav_menu_anonymous_user_gets_empty_menu(app, nav_module, monkeypatch):
    navbar = _menu(app, nav_module, monkeypatch, roles=(), is_authenticated=False)
    assert navbar.items == []


def test_nav_menu_authenticated_no_roles_gets_common_items_only(app, nav_module, monkeypatch):
    navbar = _menu(app, nav_module, monkeypatch, roles=())
    endpoints = _endpoints(navbar)

    assert 'admin.home' in endpoints
    assert 'security.change_password' in endpoints
    assert 'frontend.routes' in endpoints
    assert 'admin.sysinfo' in endpoints
    assert 'admin.routetable' not in endpoints
    assert _subgroup(navbar, 'Icons') is None
    assert _subgroup(navbar, 'Super') is None


def test_nav_menu_no_interest_hides_interest_scoped_items(app, nav_module, monkeypatch):
    navbar = _menu(app, nav_module, monkeypatch, roles=(ROLE_SUPER_ADMIN,), interest=None)
    endpoints = _endpoints(navbar)

    assert 'admin.routetable' not in endpoints
    assert 'frontend.routes' not in endpoints
    assert _subgroup(navbar, 'Icons') is None
    # super-admin items aren't interest-scoped
    assert _subgroup(navbar, 'Super') is not None


def test_nav_menu_routes_admin_sees_edit_routes(app, nav_module, monkeypatch):
    navbar = _menu(app, nav_module, monkeypatch, roles=(ROLE_ROUTES_ADMIN,))
    assert 'admin.routetable' in _endpoints(navbar)
    assert _subgroup(navbar, 'Icons') is None


def test_nav_menu_icon_admin_sees_icons_subgroup(app, nav_module, monkeypatch):
    navbar = _menu(app, nav_module, monkeypatch, roles=(ROLE_ICON_ADMIN,))
    icons = _subgroup(navbar, 'Icons')
    assert icons is not None
    icon_endpoints = [item.endpoint for item in icons.items]
    assert icon_endpoints == ['admin.iconlocations', 'admin.iconmap', 'admin.icons', 'admin.iconsubtypes']
    assert 'admin.routetable' not in _endpoints(navbar)


def test_nav_menu_super_admin_sees_everything(app, nav_module, monkeypatch):
    navbar = _menu(app, nav_module, monkeypatch, roles=(ROLE_SUPER_ADMIN,))
    endpoints = _endpoints(navbar)

    assert 'admin.routetable' in endpoints
    assert _subgroup(navbar, 'Icons') is not None
    super_group = _subgroup(navbar, 'Super')
    assert super_group is not None
    super_endpoints = [item.endpoint for item in super_group.items]
    assert super_endpoints == [
        'userrole.users', 'userrole.roles', 'userrole.interests', 'admin.files', 'admin.debug',
    ]
