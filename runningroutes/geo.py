###########################################################################################
# geo - geo functions, classes
#
#       Date            Author          Reason
#       ----            ------          ------
#       02/08/20        Lou King        Create
#
#   Copyright 2020 Lou King.  All rights reserved
###########################################################################################

'''
geo - geo functions, classes
=================================
'''
# standard
from datetime import datetime, timedelta

# pypi
from googlemaps.client import Client

# homegrown
from .models import db, Location

########################################################################
class GmapsLoc():
    # ----------------------------------------------------------------------
    def __init__(self, api_key, logger=None):
        '''
        location management

        :param api_key: google maps api key
        '''
        # see https://developers.google.com/maps/documentation/elevation/usage-limits
        # used for google maps geocoding
        self.gmapsclient = Client(key=api_key, queries_per_second=50)

        self.logger = logger

    # ----------------------------------------------------------------------
    def loc2latlng(self, loc):
        '''
        convert location to (lat, lng)

        :param loc: location address or string 'lat, lng'
        :return: [float(lat), float(lng)]
        '''

        ## if 'lat, lng', i.e., exactly two floating point numbers separated by comma
        try:
            checkloc = loc.split(', ')
            if len(checkloc) != 2: raise ValueError
            latlng = [float(l) for l in checkloc]

        ## get lat, lng from google maps API
        except ValueError:
            if self.logger: self.logger.debug('snaploc() looking up loc = {}'.format(loc))
            # assume first location is best
            geoloc = self.gmapsclient.geocode(loc)[0]
            lat = float(geoloc['geometry']['location']['lat'])
            lng = float(geoloc['geometry']['location']['lng'])
            latlng = [lat, lng]

        return latlng

    def get_location(self, location, loc_id, cache_limit):
        '''
        get current lat, lng for location, update cache if needed

        caller must verify location text is the same. If not the loc_id should
        be deleted first and loc_id=None should be passed in to create a new
        Location record.

        :param location: text location
        :param loc_id: possible location id, may be 0 or null if not set yet
        :param cache_limit: number of days in cache before needs to be recached
        :return: {'id': thisloc.id, 'coordinates': [thisloc.lat, thisloc.lng]}
        '''
        # check location for lat, lng
        checkloc = location.split(', ')
        # check for lat, long
        geoloc_required = True
        if len(checkloc) == 2:
            geoloc_required = False
            lat = checkloc[0]
            lng = checkloc[1]

        # loc_id may be 0 or null, meaning the location isn't set
        if not loc_id:
            thisloc = Location(location=location, geoloc_required=geoloc_required)
            db.session.add(thisloc)
            # check for lat, long
            if not geoloc_required:
                thisloc.lat = lat
                thisloc.lng = lng

        # loc_id was set, get the record
        else:
            thisloc = Location.query.filter_by(id=loc_id).one()

        if not thisloc.geoloc_required:
            # save everything and return the data
            db.session.commit()
            return {'id': thisloc.id, 'coordinates': [thisloc.lat, thisloc.lng]}

        # if we reach here, cache check is required
        now = datetime.now()

        # if we need to reload the cache, do it
        if not thisloc.cached or (now - thisloc.cached) > timedelta(cache_limit):
            thisloc.cached = now
            geoloc = self.gmapsclient.geocode(location)[0]
            lat = float(geoloc['geometry']['location']['lat'])
            lng = float(geoloc['geometry']['location']['lng'])
            thisloc.lat = lat
            thisloc.lng = lng

        # save everything and return the data
        db.session.commit()
        return {'id': thisloc.id, 'coordinates': [thisloc.lat, thisloc.lng]}

    def check_location(self, location):
        try:
            geoloc = self.gmapsclient.geocode(location)
            if len(geoloc) > 0:
                return True
            else:
                return False
        except:
            return False



