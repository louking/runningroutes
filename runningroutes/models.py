###########################################################################################
# models - database models for runningroutes database
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/04/19        Lou King        Create
#
#   Copyright 2019 Lou King.  All rights reserved
###########################################################################################

# standard
import os.path
from copy import deepcopy

# pypi
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from flask import current_app

class parameterError(Exception): pass

# set up database - SQLAlchemy() must be done after app.config SQLALCHEMY_* assignments
from loutilities.user.model import db, LocalUserMixin, ManageLocalTables, EMAIL_LEN

Table = db.Table
Column = db.Column
Integer = db.Integer
Float = db.Float
Boolean = db.Boolean
String = db.String
Text = db.Text
Date = db.Date
Time = db.Time
DateTime = db.DateTime
Sequence = db.Sequence
Enum = db.Enum
UniqueConstraint = db.UniqueConstraint
ForeignKey = db.ForeignKey
relationship = db.relationship
backref = db.backref
object_mapper = db.object_mapper
Base = db.Model

# LiberalBoolean - see https://github.com/spotify/luigi/issues/2347#issuecomment-505571620
from sqlalchemy import TypeDecorator
class LiberalBoolean(TypeDecorator):
    impl = Boolean

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = bool(int(value))
        return value

# some string sizes
DESCR_LEN = 512
INTEREST_LEN = 32
ROUTENAME_LEN = 256
LATLNG_LEN = 32
SURFACE_LEN = 16
FILEID_LEN = 50
FILENAME_LEN = 256
MIMETYPE_LEN = 256  # hopefully overkill - see https://tools.ietf.org/html/rfc6838#section-4.2
URL_LEN = 2047      # https://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
TURN_LEN = 256
GPXROW_LEN = 256
ICONPAGE_LEN = 2048

# icons
ICONNAME_LEN = 32
ICONSUBTYPE_LEN = 32
ICONLEGEND_LEN = 64
COLOR_LEN = 32
LOCNAME_LEN = 64
LOCATION_LEN = 256
PHONE_LEN = 16
TITLE_LEN = 32
ADDL_TEXT_LEN = 64

# role management, some of these are overloaded
USERROLEDESCR_LEN = 512
ROLENAME_LEN = 32
EMAIL_LEN = 100
NAME_LEN = 256
PASSWORD_LEN = 255
UNIQUIFIER_LEN = 255


ROLE_SUPER_ADMIN = 'super-admin'
# TODO: change to routes-admin ROLE_ROUTES_ADMIN
ROLE_ROUTES_ADMIN = 'routes-admin'
ROLE_ICON_ADMIN = 'icon-admin'

# fake route name for "route" for icon files
ICON_FILE_ROUTE = '***iconfile***'

# application specific stuff

class Route(Base):
    __tablename__ = 'route'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship("LocalInterest")
    gpx_file_id         = Column(String(FILEID_LEN))
    path_file_id        = Column(String(FILEID_LEN))
    name                = Column(String(ROUTENAME_LEN))
    distance            = Column(Float)
    start_location      = Column(String(LATLNG_LEN))
    latlng              = Column(String(LATLNG_LEN))
    surface             = Column(String(SURFACE_LEN))
    elevation_gain      = Column(Integer)
    map                 = Column(String(URL_LEN))
    description         = Column(String(DESCR_LEN))
    turns               = Column(Text)
    active              = Column(LiberalBoolean)

class Files(Base):
    __tablename__ = 'files'
    id                  = Column(Integer(), primary_key=True)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship("LocalInterest")
    route_id            = Column(Integer, ForeignKey('route.id'))
    route               = relationship("Route")
    fileid              = Column(String(FILEID_LEN))
    filename            = Column(String(FILENAME_LEN))
    mimetype            = Column(String(MIMETYPE_LEN))

class Icon(Base):
    __tablename__ = 'icon'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship("LocalInterest")
    icon                = Column(String(ICONNAME_LEN))      # text for table / pop-up / pick-list
    legend_text         = Column(String(ICONLEGEND_LEN))    # text for legend (if different from icon)
    svg_file_id         = Column(String(FILEID_LEN))
    color               = Column(String(COLOR_LEN))
    isShownOnMap        = Column(Boolean)                   # true if default is to show on *route* map
    isShownInTable      = Column(Boolean)                   # true if default is to show in table on icon map
    isAddrShown         = Column(Boolean)                   # true if location_popup_text should be shown in popup

class IconSubtype(Base):
    __tablename__ = 'iconsubtype'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship("LocalInterest")
    iconsubtype         = Column(String(ICONSUBTYPE_LEN))

class Location(Base):
    __tablename__ = 'location'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    location            = Column(String(LOCATION_LEN))      # location for map placement
    geoloc_required     = Column(Boolean, default=True)
    cached              = Column(DateTime)  # 30 day cache limit per https://cloud.google.com/maps-platform/terms/maps-service-terms
                                            # only set if geoloc_required is True
    lat                 = Column(Float)
    lng                 = Column(Float)

class IconLocation(Base):
    __tablename__ = 'iconlocation'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship("LocalInterest")
    locname             = Column(String(LOCNAME_LEN))
    icon_id             = Column(Integer, ForeignKey('icon.id'))
    icon                = relationship("Icon")
    iconsubtype_id      = Column(Integer, ForeignKey('iconsubtype.id'))
    iconsubtype         = relationship("IconSubtype")
    location_id         = Column(Integer, ForeignKey('location.id'))
    location            = relationship("Location")
    location_popup_text = Column(String(LOCATION_LEN))      # location for pop-up
    contact_name        = Column(String(NAME_LEN))
    email               = Column(String(EMAIL_LEN))
    phone               = Column(String(PHONE_LEN))
    addl_text           = Column(String(ADDL_TEXT_LEN))

class IconMap(Base):
    __tablename__ = 'iconmap'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship("LocalInterest")
    page_title          = Column(String(TITLE_LEN))
    page_description    = Column(String(ICONPAGE_LEN))     # markdown description for head of page, with {legend} understood
    location_id         = Column(Integer, ForeignKey('location.id'))
    location            = relationship("Location")

# copied by update_local_tables
class LocalUser(LocalUserMixin, Base):
    __tablename__ = 'localuser'
    id                  = Column(Integer(), primary_key=True)
    interest_id         = Column(Integer, ForeignKey('localinterest.id'))
    interest            = relationship('LocalInterest', backref=backref('users'))
    version_id          = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {
        'version_id_col' : version_id
    }

# note update_local_tables only copies Interests for current application (g.loutility)
class LocalInterest(Base):
    __tablename__ = 'localinterest'
    id                  = Column(Integer(), primary_key=True)
    interest_id         = Column(Integer)

    version_id          = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {
        'version_id_col' : version_id
    }


#####################################################
class priorityUpdater(): 
#####################################################
    # increment priority for each of the blocks
    def __init__(self, initial, increment):
        self.priority = initial - increment
        self.increment = increment

    def __call__(self):
        self.priority += self.increment
        return self.priority

#####################################################
class ModelItem():
#####################################################
    '''
    used within dbinit_xx modules 

    :param model: database model to initialize
    :param items: list of item objects, with object keys matching column names
        item object value may be function with no parameters to resolve at runtime
    :param cleartable: False if items are to be merged. True if table is to be cleared before initializing.
        default True
    :param checkkeys: if cleartable == False, list of keys to check to decide if record is 
        to be added. If there is a record in the table with values matching this item's for these
        keys, the record is updated.
        Alternately, a function can be supplied f(item) to check against db, returns the record
        if item found, None otherwise. For convenience, scalar key can be supplied (i.e., not a list).

        if key has '/', this means dbfield/itemkey, where itemkey may be dotted notation.
        E.g., race_id/race.id
    '''

    #----------------------------------------------------------------------
    def __init__(self, model, items, cleartable=True, checkkeys=[]):
    #----------------------------------------------------------------------
        self.model = model
        self.items = items
        self.cleartable = cleartable
        self.checkkeys = checkkeys

#####################################################
class getmodelitems():
#####################################################
    #----------------------------------------------------------------------
    def __init__(self, model, queries):
    #----------------------------------------------------------------------
        '''
        returns a (class) function to retrieve a model item or items based on value, at runtime

        :param model: model to retrieve from
        :param queries: query dicts to retrieve with
            if queries is a list of dicts, returned function will return a list
            if queries is a dict, returned function will return a value
        '''
        self.model = model
        self.queries = queries

    #----------------------------------------------------------------------
    def __call__(self):
    #----------------------------------------------------------------------
        '''
        class instance behaves as a function f, use f() to call
        '''
        # islist = isinstance(self.vals, list)
        islist = isinstance(self.queries, list)

        # will process as list now, but will remove list later
        if islist:
            queries = self.queries
        else:
            queries = [self.queries]

        items = []
        # for val in vals:
        for query in queries:
            thisquery = deepcopy(query)

            # resolve any callable values in query
            for attr in thisquery:
                if callable(thisquery[attr]):
                    thisquery[attr] = thisquery[attr]()

            item = db.session.query(self.model).filter_by(**thisquery).one()
            items.append(item)

        # return list if vals was list
        if islist:
            return items
        else:
            return items[0]

# supporting functions
def update_local_tables():
    '''
    keep LocalUser table consistent with external db User table
    '''
    # appname needs to match Application.application
    localtables = ManageLocalTables(db, 'routes', LocalUser, LocalInterest, hasuserinterest=True)
    localtables.update()

