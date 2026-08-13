'''
test_frontend_icons - test runningroutes.views.frontend.icons
=========================================================

views/frontend/icons.py does `from runningroutes import app` and builds a real GmapsLoc at
*module import time* -- see test_locations.py/test_frontend.py for the same pattern and why the
frontend_icons_module fixture below defers the import until after the `app` fixture has run.
'''

# standard
import xml.etree.ElementTree as ET

# pypi
import pytest
from flask import g

# homegrown
from runningroutes.files import create_fidfile
from runningroutes.models import db, LocalInterest, Icon, IconLocation, Location
from loutilities.user.model import Interest

from fakecurrentuser import FakeCurrentUser

SVG_CONTENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">'
    '<path fill="#123456" d="M12 2L2 22h20z"/>'
    '</svg>'
)


@pytest.fixture
def frontend_icons_module(app):
    from runningroutes.views.frontend import icons
    return icons


@pytest.fixture
def iconlocationsetup(dbapp, tmp_path, monkeypatch):
    monkeypatch.setitem(dbapp.config, 'APP_FILE_FOLDER', str(tmp_path / 'files'))

    interest = Interest(interest='fsrc', description='FSRC', public=True)
    db.session.add(interest)
    db.session.commit()
    linterest = LocalInterest(interest_id=interest.id)
    db.session.add(linterest)
    db.session.commit()

    svg_fid, svg_path = create_fidfile('fsrc', 'marker.svg', 'image/svg+xml')
    with open(svg_path, 'w') as f:
        f.write(SVG_CONTENT)

    icon = Icon(interest_id=linterest.id, icon='store', svg_file_id=svg_fid, color='red',
                isShownOnMap=True, isShownInTable=True, isAddrShown=False)
    db.session.add(icon)
    db.session.commit()

    loc = Location(location='123 Main St', geoloc_required=True)
    db.session.add(loc)
    db.session.commit()

    iconloc = IconLocation(interest_id=linterest.id, locname='Some Store', icon_id=icon.id,
                            location_id=loc.id)
    db.session.add(iconloc)
    db.session.commit()

    return {'interest': interest, 'linterest': linterest, 'icon': icon, 'location': loc,
            'iconlocation': iconloc}


def test_iconlocations_beforequery_sets_interest_id(iconlocationsetup, frontend_icons_module, app):
    with app.test_request_context():
        g.interest = 'fsrc'
        view = frontend_icons_module.IconLocations()
        view.beforequery()
        assert view.queryparams == {'interest_id': iconlocationsetup['linterest'].id}


def test_iconlocations_permission_delegates_to_check_permission(
        iconlocationsetup, frontend_icons_module, monkeypatch, app):
    # check_permission()/current_user live in views.frontend.frontend -- icons.py imports the
    # function directly (`from .frontend import check_permission`), not current_user
    from runningroutes.views.frontend import frontend as frontend_module
    monkeypatch.setattr(frontend_module, 'current_user', FakeCurrentUser(is_authenticated=False))
    with app.test_request_context():
        g.interest = 'fsrc'
        assert frontend_icons_module.IconLocations().permission() is True


def test_retrieverows_no_interest_returns_fail_status(dbapp, frontend_icons_module, app):
    with app.test_request_context():
        g.interest = None
        view = frontend_icons_module.IconLocations()
        view.queryparams = {}
        resp = view._retrieverows(rest=True)
        assert resp.get_json()['status'] == 'FAIL'


def test_retrieverows_parses_svg_and_geocodes(iconlocationsetup, frontend_icons_module, app, monkeypatch):
    monkeypatch.setattr(frontend_icons_module.gmaps, 'get_location',
                         lambda location, loc_id, cache_limit: {'id': loc_id, 'coordinates': [39.1, -77.1]})

    with app.test_request_context():
        g.interest = 'fsrc'
        view = frontend_icons_module.IconLocations()
        view.queryparams = {'interest_id': iconlocationsetup['linterest'].id}
        features = view._retrieverows(rest=False)

    assert len(features) == 1
    feature = features[0]
    assert feature['geometry']['coordinates'] == [39.1, -77.1]
    props = feature['geometry']['properties']
    assert props['name'] == 'Some Store'
    assert props['path'] == 'M12 2L2 22h20z'
    assert props['iconattrs']['icon'] == 'store'
    assert props['type'] == 'store'


def test_retrieverows_rest_filters_by_isshownintable(iconlocationsetup, frontend_icons_module, app, monkeypatch):
    iconlocationsetup['icon'].isShownInTable = False
    db.session.commit()
    monkeypatch.setattr(frontend_icons_module.gmaps, 'get_location',
                         lambda location, loc_id, cache_limit: {'id': loc_id, 'coordinates': [39.1, -77.1]})

    with app.test_request_context():
        g.interest = 'fsrc'
        view = frontend_icons_module.IconLocations()
        view.queryparams = {'interest_id': iconlocationsetup['linterest'].id}
        resp = view._retrieverows(rest=True)

    assert resp.get_json()['features'] == []
