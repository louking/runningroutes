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
db = SQLAlchemy()
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
ROLE_INTEREST_ADMIN = 'interest-admin'
ROLE_ICON_ADMIN = 'icon-admin'

# fake route name for "route" for icon files
ICON_FILE_ROUTE = '***iconfile***'

# application specific stuff

userinterest_table = Table('users_interests', Base.metadata,
                          Column('user_id', Integer, ForeignKey('user.id')),
                          Column('interest_id', Integer, ForeignKey('interest.id'))
                          )

class Interest(Base):
    __tablename__ = 'interest'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest            = Column(String(INTEREST_LEN))
    users               = relationship("User",
                                       secondary=userinterest_table,
                                       backref=backref("interests"))
    description         = Column(String(DESCR_LEN))
    public              = Column(Boolean)

class Route(Base):
    __tablename__ = 'route'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('interest.id'))
    interest            = relationship("Interest")
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
    interest_id         = Column(Integer, ForeignKey('interest.id'))
    interest            = relationship("Interest")
    route_id            = Column(Integer, ForeignKey('route.id'))
    route               = relationship("Route")
    fileid              = Column(String(FILEID_LEN))
    filename            = Column(String(FILENAME_LEN))
    mimetype            = Column(String(MIMETYPE_LEN))

class Icon(Base):
    __tablename__ = 'icon'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    interest_id         = Column(Integer, ForeignKey('interest.id'))
    interest            = relationship("Interest")
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
    interest_id         = Column(Integer, ForeignKey('interest.id'))
    interest            = relationship("Interest")
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
    interest_id         = Column(Integer, ForeignKey('interest.id'))
    interest            = relationship("Interest")
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
    interest_id         = Column(Integer, ForeignKey('interest.id'))
    interest            = relationship("Interest")
    page_title          = Column(String(TITLE_LEN))
    page_description    = Column(String(DESCR_LEN))     # markdown description for head of page, with {legend} understood

# user role management
# adapted from 
#   https://flask-security-too.readthedocs.io/en/stable/quickstart.html (SQLAlchemy Application)

class RolesUsers(Base):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))

class Role(Base, RoleMixin):
    __tablename__ = 'role'
    id                  = Column(Integer(), primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    name                = Column(String(ROLENAME_LEN), unique=True)
    description         = Column(String(USERROLEDESCR_LEN))

class User(Base, UserMixin):
    __tablename__ = 'user'
    id                  = Column(Integer, primary_key=True)
    version_id          = Column(Integer, nullable=False, default=1)
    email               = Column( String(EMAIL_LEN), unique=True )  # = username
    password            = Column( String(PASSWORD_LEN) )
    name                = Column( String(NAME_LEN) )
    given_name          = Column( String(NAME_LEN) )
    last_login_at       = Column( DateTime() )
    current_login_at    = Column( DateTime() )
    last_login_ip       = Column( String(100) )
    current_login_ip    = Column( String(100) )
    login_count         = Column( Integer )
    active              = Column( Boolean() )
    fs_uniquifier       = Column( String(UNIQUIFIER_LEN) )
    confirmed_at        = Column( DateTime() )
    roles               = relationship('Role', secondary='roles_users',
                          backref=backref('users', lazy='dynamic'))


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


#----------------------------------------------------------------------
def initdbmodels(modelitems):
#----------------------------------------------------------------------
    '''
    initialize database models

    :param modelitems: list of ModelItem objects
    '''
    # clear desired tables in reverse order to avoid constraint errors
    clearmodels = [mi.model for mi in modelitems if mi.cleartable]
    clearmodels.reverse()
    for model in clearmodels:
        for modelrow in db.session.query(model).all():
            current_app.logger.debug('deleting id={} modelrow={}'.format(modelrow.id, modelrow.__dict__))
            db.session.delete(modelrow)

    # build tables
    for modelitem in modelitems:
        model = modelitem.model

        # maybe items is list of strings, like csv file
        if len(modelitem.items) > 0 and isinstance(modelitem.items[0], basestring):
            from csv import DictReader
            ITEMS = DictReader(modelitem.items)
            items = []
            for item in ITEMS:
                items.append(item)
        
        # otherwise assume items are objects
        else:
            items = modelitem.items

        cleartable = modelitem.cleartable
        checkkeys = modelitem.checkkeys

        # if caller supplied function to check item existence, use it
        if callable(checkkeys):
            itemexists = checkkeys
        
        # otherwise, checkkeys is list of keys to filter, create function to check
        else:
            # allow scalar
            if type(checkkeys) != list:
                checkkeys = [checkkeys]

            def itemexists(item):
                query = {}
                # for top level keys, just add to top level query
                # for secondary keys add additional filters 
                # note only allows two levels, and is a bit brute force
                for key in checkkeys:
                    keys = key.split('/')

                    # just a key here
                    if len(keys) == 1:
                        query[key] = item[key]
                    
                    # something like race_id/race.id, where race_id is attribute of model, race is key of item, and id is attribute of race
                    elif len(keys) == 2:
                        modelid, dottedkeys = keys
                        thiskey, thisattr = dottedkeys.split('.')
                        query[modelid] = getattr(item[thiskey], thisattr)
                    
                    # bad configuration, like x/y/z
                    else:
                        raise parameterError('invalid key has too many parts: {}, item {}'.format(key, item))


                # return query result
                thisquery = model.query.filter_by(**query)
                return thisquery.one_or_none()

        for item in items:
            resolveitem = {}
            for key in item:
                if not callable(item[key]):
                    resolveitem[key] = item[key]
                else:
                    resolveitem[key] = item[key]()

            if not cleartable:
                thisitem = itemexists(resolveitem)
            
            # maybe we need to add
            # note thisitem not initialized if cleartable
            if cleartable or not thisitem:
                current_app.logger.info( 'initdbmodels(): adding {}'.format(resolveitem) )
                db.session.add( model(**resolveitem) )
            
            # if item exists, update it with resolved data
            elif thisitem:
                current_app.logger.info( 'initdbmodels(): updating old: {}, new: {}'.format(thisitem.__dict__, resolveitem) )
                # thisitem.__dict__.update(resolveitem)
                for key in resolveitem:
                    setattr(thisitem, key, resolveitem[key])


        # need to commit within loop because next model might use this model's data
        db.session.commit()
