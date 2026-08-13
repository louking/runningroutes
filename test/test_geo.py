'''
test_geo - test runningroutes.geo
=========================================================
'''

# standard
from datetime import datetime, timedelta

# pypi
import pytest

# homegrown
from runningroutes.geo import isLatlng, GmapsLoc
from runningroutes.models import db, Location


# ----------------------------------------------------------------------
# isLatlng
# ----------------------------------------------------------------------

@pytest.mark.parametrize('latlng', [
    '39.4143, -77.4103',
    '39.4143,-77.4103',
    '-39.4143, 77.4103',
    '0, 0',
    '90, 180',
    '-90, -180',
])
def test_islatlng_true_for_valid_coordinates(latlng):
    assert isLatlng(latlng) is True


@pytest.mark.parametrize('notlatlng', [
    '123 Main St, Frederick, MD',
    '91, 0',       # lat out of range
    '0, 181',       # lng out of range
    'not a location',
    '',
])
def test_islatlng_false_for_non_coordinates(notlatlng):
    assert isLatlng(notlatlng) is False


# ----------------------------------------------------------------------
# GmapsLoc.loc2latlng
# ----------------------------------------------------------------------

@pytest.fixture
def gmapsloc():
    return GmapsLoc(api_key='AIzaFakeTestKey0000000000000000000')


def test_loc2latlng_parses_lat_lng_string_without_geocoding(gmapsloc, monkeypatch):
    def fail_geocode(*args, **kwargs):
        raise AssertionError('geocode() should not be called for a lat,lng string')
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode', fail_geocode)

    assert gmapsloc.loc2latlng('39.4143, -77.4103') == [39.4143, -77.4103]


def test_loc2latlng_geocodes_address(gmapsloc, monkeypatch):
    calls = []
    def fake_geocode(address):
        calls.append(address)
        return [{'geometry': {'location': {'lat': 39.4143, 'lng': -77.4103}}}]
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode', fake_geocode)

    assert gmapsloc.loc2latlng('123 Main St, Frederick, MD') == [39.4143, -77.4103]
    assert calls == ['123 Main St, Frederick, MD']


# ----------------------------------------------------------------------
# GmapsLoc.check_location
# ----------------------------------------------------------------------

def test_check_location_true_when_geocode_returns_results(gmapsloc, monkeypatch):
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode',
                         lambda address: [{'geometry': {'location': {'lat': 1, 'lng': 1}}}])
    assert gmapsloc.check_location('somewhere') is True


def test_check_location_false_when_geocode_returns_no_results(gmapsloc, monkeypatch):
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode', lambda address: [])
    assert gmapsloc.check_location('nowhere') is False


def test_check_location_false_when_geocode_raises(gmapsloc, monkeypatch):
    def raise_error(address):
        raise ValueError('boom')
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode', raise_error)
    assert gmapsloc.check_location('anything') is False


# ----------------------------------------------------------------------
# GmapsLoc.get_location
# ----------------------------------------------------------------------

def test_get_location_lat_lng_string_creates_location_without_geocoding(gmapsloc, bare_dbapp, monkeypatch):
    def fail_geocode(*args, **kwargs):
        raise AssertionError('geocode() should not be called for a lat,lng location')
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode', fail_geocode)

    result = gmapsloc.get_location('39.4143, -77.4103', None, 30)

    loc = Location.query.filter_by(id=result['id']).one()
    assert loc.geoloc_required is False
    assert result['coordinates'] == [39.4143, -77.4103]


def test_get_location_new_address_geocodes_and_caches(gmapsloc, bare_dbapp, monkeypatch):
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode',
                         lambda address: [{'geometry': {'location': {'lat': 39.4143, 'lng': -77.4103}}}])

    result = gmapsloc.get_location('123 Main St', None, 30)

    loc = Location.query.filter_by(id=result['id']).one()
    assert loc.geoloc_required is True
    assert loc.cached is not None
    assert result['coordinates'] == [39.4143, -77.4103]


def test_get_location_reuses_cache_within_limit(gmapsloc, bare_dbapp, monkeypatch):
    loc = Location(location='123 Main St', geoloc_required=True, lat=1.0, lng=2.0, cached=datetime.now())
    db.session.add(loc)
    db.session.commit()

    def fail_geocode(*args, **kwargs):
        raise AssertionError('geocode() should not be called when cache is still valid')
    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode', fail_geocode)

    result = gmapsloc.get_location('123 Main St', loc.id, 30)

    assert result['coordinates'] == [1.0, 2.0]


def test_get_location_recaches_when_stale(gmapsloc, bare_dbapp, monkeypatch):
    stale = datetime.now() - timedelta(days=31)
    loc = Location(location='123 Main St', geoloc_required=True, lat=1.0, lng=2.0, cached=stale)
    db.session.add(loc)
    db.session.commit()

    monkeypatch.setattr(gmapsloc.gmapsclient, 'geocode',
                         lambda address: [{'geometry': {'location': {'lat': 9.0, 'lng': 8.0}}}])

    result = gmapsloc.get_location('123 Main St', loc.id, 30)

    assert result['coordinates'] == [9.0, 8.0]
