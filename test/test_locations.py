'''
test_locations - test runningroutes.locations
=========================================================

locations.py does `from . import app` and builds a real GmapsLoc/googlemaps.Client at *module
import time* -- this only works once runningroutes.app (the module global set inside
create_app()) is a real Flask app, i.e. after create_app() has run at least once. Since Python
only executes a module body on its first import, and the `app` fixture (conftest.py) builds the
real app exactly once per session, `locations` must not be imported at test-file collection time
(before any fixture has run) -- the locations_module fixture below defers the import until after
the `app` fixture has executed, at which point it's already sitting in sys.modules.
'''

# pypi
import pytest

# homegrown
from runningroutes.models import db, IconLocation


@pytest.fixture
def locations_module(app):
    import runningroutes.locations as locations_module
    return locations_module


# ----------------------------------------------------------------------
# location_validate
# ----------------------------------------------------------------------

def test_location_validate_missing_location_is_required(locations_module):
    errors = locations_module.location_validate('create', {})
    assert errors == [{'name': 'location', 'status': 'location is required'}]


def test_location_validate_empty_location_is_required(locations_module):
    errors = locations_module.location_validate('create', {'location': ''})
    assert errors == [{'name': 'location', 'status': 'location is required'}]


def test_location_validate_valid_location_passes(locations_module, monkeypatch):
    monkeypatch.setattr(locations_module.gmaps, 'check_location', lambda loc: True)
    errors = locations_module.location_validate('create', {'location': '123 Main St'})
    assert errors == []


def test_location_validate_unparseable_location_fails(locations_module, monkeypatch):
    monkeypatch.setattr(locations_module.gmaps, 'check_location', lambda loc: False)
    errors = locations_module.location_validate('create', {'location': 'gibberish'})
    assert errors == [{'name': 'location', 'status': 'location could not be parsed by google maps'}]


# ----------------------------------------------------------------------
# get_location
# ----------------------------------------------------------------------

def test_get_location_returns_empty_string_when_no_location_id(dbapp, locations_module):
    dbrow = IconLocation(location_id=None)
    assert locations_module.get_location(dbrow) == ''


def test_get_location_returns_location_text(dbapp, locations_module):
    from runningroutes.models import Location
    loc = Location(location='123 Main St')
    db.session.add(loc)
    db.session.commit()

    dbrow = IconLocation(location_id=loc.id)
    db.session.add(dbrow)
    db.session.commit()

    assert locations_module.get_location(dbrow) == '123 Main St'
