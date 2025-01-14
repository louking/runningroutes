###########################################################################################
# locations - location administration
#
#       Date            Author          Reason
#       ----            ------          ------
#       02/18/20        Lou King        Create
#
#   Copyright 2020 Lou King.  All rights reserved
###########################################################################################

# standard

# home grown
from . import app
from .geo import GmapsLoc

# set up for google maps location management
gmaps = GmapsLoc(app.config['GMAPS_ELEV_API_KEY'])

# functions used by MethodView classes which use IconLocationCrud
# validate location subrecord
def location_validate(action, formdata):
    results = []

    if 'location' not in formdata or not formdata['location']:
        results.append({ 'name' : 'location', 'status' : 'location is required' })

    else:
        if formdata['location'] and not gmaps.check_location(formdata['location']):
            results.append({ 'name' : 'location', 'status' : 'location could not be parsed by google maps' })

    return results

# retrieve location from database for initial display
# see IconsLocationsCrud.editor_method_posthook() for editor create/update of location
def get_location(dbrow):
    if not dbrow.location_id:
        loc = ''
    else:
        loc = dbrow.location.location
    return loc
