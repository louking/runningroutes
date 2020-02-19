###########################################################################################
# icons - administrative views for runningroutes database, icons management
#
#       Date            Author          Reason
#       ----            ------          ------
#       02/05/20        Lou King        Create
#
#   Copyright 2020 Lou King.  All rights reserved
###########################################################################################

# standard
from copy import deepcopy

# pypi
from flask import g, request, render_template
from flask_security import current_user, auth_required

# homegrown
from . import bp
from runningroutes import app
from runningroutes.models import db, Files, Role, Interest, IconMap, Icon, IconSubtype, IconLocation, Route, Location
from runningroutes.models import ICON_FILE_ROUTE
from runningroutes.files import create_fidfile
from runningroutes.models import ROLE_SUPER_ADMIN, ROLE_ICON_ADMIN
from runningroutes.geo import GmapsLoc
from runningroutes.locations import get_location, location_validate
from loutilities.tables import CrudFiles, DbCrudApiRolePermissions, get_request_action, get_request_data

debug = False

# set up for google maps location management
gmaps = GmapsLoc(app.config['GMAPS_ELEV_API_KEY'])

#######################################################################
class IconsCrud(DbCrudApiRolePermissions):
    decorators = [auth_required()]

    # ----------------------------------------------------------------------
    def permission(self):
        '''
        check for permission on data
        :rtype: boolean
        '''
        if debug: print('IconsCrud.permission()')

        # check details on whether the user has permission to edit icons
        # need to be logged in
        if not current_user.is_authenticated:
            return False

        # g.interest initialized in runningroutes.create_app.pull_interest
        # g.interest contains slug, pull in interest db entry. If not found, no permission granted
        self.interest = Interest.query.filter_by(interest=g.interest).one_or_none()

        # If no interest was found, no permission granted
        if not self.interest:
            return False

        # is someone logged in with ROLE_SUPER_ADMIN role? They're good
        superadmin = Role.query.filter_by(name=ROLE_SUPER_ADMIN).one()
        if superadmin in current_user.roles:
            return True

        # if they're not logged in with ROLE_ICON_ADMIN role, they're bad
        iconadmin = Role.query.filter_by(name=ROLE_ICON_ADMIN).one()
        if not iconadmin in current_user.roles:
            return False

        # current_user has ROLE_ICON_ADMIN. Can this user access current interest?
        if self.interest in current_user.interests:
            return True
        else:
            return False

    # ----------------------------------------------------------------------
    def beforequery(self):
        '''
        filter on current interest
        :return:
        '''
        interest = Interest.query.filter_by(interest=g.interest).one()
        self.queryparams['interest_id'] = interest.id

    # ----------------------------------------------------------------------
    def set_files_icon(self, fileidlist=[]):
        '''
        leaves files in fileidlist as pointing to specified route
        caller must flush / commit

        :param fileidlist: list of file ids to set to leaving pointing at current route,
            leave empty when deleting route
        :return: None
        '''
        fakeroute = Route.query.filter_by(name=ICON_FILE_ROUTE).one()
        for fileid in fileidlist:
            file = Files.query.filter_by(fileid=fileid).one()
            file.route_id = fakeroute.id

    # ----------------------------------------------------------------------
    def createrow(self, formdata):
        '''
        creates row in database

        :param formdata: data from create form
        :rtype: returned row for rendering, e.g., from DataTablesEditor.get_response_data()
        '''
        if debug: print('IconsCrud.createrow()')

        # make sure we record the row's interest
        formdata['interest_id'] = self.interest.id

        # return the row
        row = super(IconsCrud, self).createrow(formdata)
        if 'svg_file_id' in row and row['svg_file_id']:
            self.set_files_icon([row['svg_file_id']])

        return row

    # ----------------------------------------------------------------------
    def updaterow(self, thisid, formdata):
        '''
        updates row in database

        :param thisid: id of row to be updated
        :param formdata: data from create form
        :rtype: returned row for rendering, e.g., from DataTablesEditor.get_response_data()
        '''
        if debug: print('IconsCrud.updaterow()')

        row = super(IconsCrud, self).updaterow(thisid, formdata)
        if 'svg_file_id' in row and row['svg_file_id']:
            self.set_files_icon([row['svg_file_id']])

        return row

    # ----------------------------------------------------------------------
    def render_template(self, **kwargs):
        '''
        renders flask template with appropriate parameters
        :param tabledata: list of data rows for rendering
        :rtype: flask.render_template()
        '''
        # the args dict has all the defined parameters to 
        # caller supplied keyword args are used to update the defaults
        # all arguments are made into attributes for self
        if debug: print('IconsCrud.render_template()')

        args = deepcopy(kwargs)

        return render_template('datatables.jinja2', **args)


#######################################################################
class IconLocationCrud(IconsCrud):
    decorators = [auth_required()]
    # TODO: is there a way to make this generic, e.g., thru use of multiple inheritance?

    # ----------------------------------------------------------------------
    def editor_method_posthook(self, form):
        '''
        check if Location subrecord needs to be created or updated

        :param form: form from editor
        :return: None
        '''

        # we process actions of 'create' or 'edit'
        action = get_request_action(form)
        formdata = get_request_data(form)

        # we're only handling create and edit actions here
        if action not in ['create', 'edit']:
            return

        # formdata should only have one key
        iformdata = iter(formdata)
        thisid = next(iformdata)

        # use the recently created record, or the one which we're updating
        if action == 'create':
            thisiconloc = self.model.query.filter_by(id=self.created_id).one()
        elif action == 'edit':
            thisiconloc = self.model.query.filter_by(id=thisid).one()
        # can't get here, but included for completeness
        else:
            return

        location = formdata[thisid]['location']
        locrec_id = thisiconloc.location_id

        if locrec_id:
            locrec = thisiconloc.location
            # if we changed the location, replace the record
            if locrec.location != location:
                thisiconloc.location_id = None
                db.session.delete(locrec)
                locrec_id = None

        locameta = gmaps.get_location(location, locrec_id, app.config['GMAPS_CACHE_LIMIT'])
        thisiconloc.location_id = locameta['id']
        # _responsedata is list, will have a single item
        self._responsedata[0]['location'] = thisiconloc.location.location

    # ----------------------------------------------------------------------
    def deleterow(self, thisid):
        '''
        deletes row in database

        :param thisid: id of row to be deleted
        :return: []
        '''

        # delete Location sub record
        dbrow = self.model.query.filter_by(id=thisid).one()
        if dbrow.location_id:
            self.db.session.delete(dbrow.location)

        # delete the row -- return what the super returns ([])
        row = super(IconLocationCrud, self).deleterow(thisid)

        return row

        # ----------------------------------------------------------------------

#######################################################################
class IconsFiles(CrudFiles):

    #----------------------------------------------------------------------
    def __init__(self, **kwargs):

        if debug: print('IconsFiles.__init__() **kwargs={}'.format(kwargs))
        self.datafolderid = None
        super(IconsFiles, self).__init__(**kwargs)
        if debug: print('IconsFiles self.app = {}'.format(self.app))


    #----------------------------------------------------------------------
    def upload(self):

        if (debug): print('IconsFiles.upload()')

        # save gpx file
        thisfile = request.files['upload']
        icon_fid, filepath = create_fidfile(g.interest, thisfile.filename, thisfile.mimetype)
        thisfile.save(filepath)
        thisfile.seek(0)

        return {
            'upload' : {'id': icon_fid },
            'files' : {
                'data' : {
                    icon_fid : {'filename': thisfile.filename}
                },
            },
            'svg_file_id' : icon_fid,
        }

    #----------------------------------------------------------------------
    def list(self):

        if (debug): print('IconsFiles.list()')

        # list files whose parent is datafolderid
        table = 'data'
        filelist = {table:{}}
        files = Files.query.all()
        for file in files:
            filelist[table][file.fileid] = {'filename': file.filename}

        return filelist

#############################################
# files handling
iconfiles = IconsFiles(
    app = bp,
    uploadendpoint = 'iconupload',
    uploadrule='/<interest>/iconupload',
)

#############################################
# icon admin views

# iconmap endpoint
iconmap_dbattrs = 'id,interest_id,page_title,page_description,location'.split(',')
iconmap_formfields = 'rowid,interest_id,page_title,page_description,location'.split(',')
iconmap_dbmapping = dict(list(zip(iconmap_dbattrs, iconmap_formfields)))
iconmap_formmapping = dict(list(zip(iconmap_formfields, iconmap_dbattrs)))
iconmap_formmapping['location'] = get_location
# db update to location happens in editor_method_posthook()
iconmap_dbmapping['location'] = None

iconmap = IconLocationCrud(app=bp,
                           db = db,
                           pagename = 'Icon Map',
                           model = IconMap,
                           checkrequired = True,
                           version_id_col='version_id',  # optimistic concurrency control
                           idSrc = 'rowid',
                           rule = '/<interest>/iconmap',
                           endpoint = 'admin.iconmap',
                           endpointvalues = {'interest':'<interest>'},
                           dbmapping = iconmap_dbmapping,
                           formmapping = iconmap_formmapping,
                           validate = location_validate,
                           buttons = ['create', 'edit'],
                           clientcolumns =  [
                        { 'name': 'page_title', 'data': 'page_title', 'label': 'Page Title',
                          'fieldInfo': 'title you want on the user icons page',
                          'className': 'field_req'
                          },
                        {'name': 'location', 'data': 'location', 'label': 'Center',
                         'className': 'field_req',
                         'fieldInfo': 'location used for map center, must work on google maps',
                         },
                        { 'name': 'page_description', 'data': 'page_description', 'type': 'textarea',
                          'label': 'Header Text',
                          'fieldInfo' : 'use MarkDown to describe what\'s on the page' },
                   ]);
iconmap.register()

# icon endpoint
icon_dbattrs = 'id,interest_id,icon,legend_text,svg_file_id,color,isShownOnMap,isShownInTable,isAddrShown'.split(',')
icon_formfields = 'rowid,interest_id,icon,legend_text,svg_file_id,color,isShownOnMap,isShownInTable,isAddrShown'.split(',')
icon_dbmapping = dict(list(zip(icon_dbattrs, icon_formfields)))
icon_formmapping = dict(list(zip(icon_formfields, icon_dbattrs)))
icon = IconsCrud(app=bp,
                 db = db,
                 pagename = 'Icons',
                 model = Icon,
                 checkrequired = True,
                 version_id_col='version_id',  # optimistic concurrency control
                 idSrc = 'rowid',
                 rule = '/<interest>/icons',
                 endpoint = 'admin.icons',
                 endpointvalues = {'interest':'<interest>'},
                 files=iconfiles,
                 eduploadoption={
                     'type': 'POST',
                     'url': '/admin/<interest>/iconupload',
                 },
                 dbmapping = icon_dbmapping,
                 formmapping = icon_formmapping,
                 buttons = ['create', 'edit', 'remove'],
                 clientcolumns =  [
                    { 'name': 'icon', 'data': 'icon', 'label': 'Icon Name',
                      'fieldInfo': 'text for table / pop-up / pick-list',
                      'className': 'field_req'
                      },
                    { 'name': 'legend_text', 'data': 'legend_text', 'label': 'Legend Text',
                      'fieldInfo' : 'text for legend (if different from icon)' },
                    {'name': 'svg_file_id', 'data': 'svg_file_id', 'label': 'Svg File',
                     'className': 'field_req',
                     'ed': {'type': 'upload',
                            'fieldInfo': 'SVG file to display as the icon',
                            'dragDrop': False,
                            'display': 'renderfileid()'},
                     'dt': {'render': 'renderfileid()'},
                     },
                     {'name': 'color', 'data': 'color', 'label': 'Color',
                      'fieldInfo': 'css supported color value',
                      'className': 'field_req',
                      },
                     {'data': 'isShownOnMap', 'name': 'isShownOnMap', 'label': 'Show on Routes Map',
                      'className': 'field_req',
                      '_treatment': {'boolean': {'formfield': 'isShownOnMap', 'dbfield': 'isShownOnMap'}}
                      },
                     {'data': 'isShownInTable', 'name': 'isShownInTable', 'label': 'Show in Icon Map Table',
                      'className': 'field_req',
                      '_treatment': {
                          'boolean': {'formfield': 'isShownInTable', 'dbfield': 'isShownInTable'}}
                      },
                     {'data': 'isAddrShown', 'name': 'isAddrShown',
                      'label': 'Show Location Text in Popup on Route',
                      'className': 'field_req',
                      '_treatment': {
                          'boolean': {'formfield': 'isAddrShown', 'dbfield': 'isAddrShown'}}
                      },
                ]);
icon.register()

# iconsubtype endpoint
iconsubtype_dbattrs = 'id,interest_id,iconsubtype'.split(',')
iconsubtype_formfields = 'rowid,interest_id,iconsubtype'.split(',')
iconsubtype_dbmapping = dict(list(zip(iconsubtype_dbattrs, iconsubtype_formfields)))
iconsubtype_formmapping = dict(list(zip(iconsubtype_formfields, iconsubtype_dbattrs)))
iconsubtype = IconsCrud(app=bp,
                        db = db,
                        pagename = 'Icon Subtypes',
                        model = IconSubtype,
                        checkrequired = True,
                        version_id_col='version_id',  # optimistic concurrency control
                        idSrc = 'rowid',
                        rule = '/<interest>/iconsubtypes',
                        endpoint = 'admin.iconsubtypes',
                        endpointvalues = {'interest':'<interest>'},
                        dbmapping = iconsubtype_dbmapping,
                        formmapping = iconsubtype_formmapping,
                        buttons = ['create', 'edit', 'remove'],
                        clientcolumns =  [
                        { 'name': 'iconsubtype', 'data': 'iconsubtype', 'label': 'Subtype',
                          'className': 'field_req'
                         },
                        ]);
iconsubtype.register()

# iconlocation endpoint
iconlocation_dbattrs = ('id,interest_id,locname,icon,iconsubtype,location,location_popup_text,contact_name,' +
                        'email,phone').split(',')
iconlocation_formfields = ('rowid,interest_id,locname,icon,iconsubtype,location,location_popup_text,contact_name,' +
                           'email,phone').split(',')
iconlocation_dbmapping = dict(list(zip(iconlocation_dbattrs, iconlocation_formfields)))
iconlocation_formmapping = dict(list(zip(iconlocation_formfields, iconlocation_dbattrs)))
iconlocation_formmapping['location'] = get_location
# db update to location happens in editor_method_posthook()
iconlocation_dbmapping['location'] = None

iconlocation = IconLocationCrud(app=bp,
                                db = db,
                                pagename = 'Icon Locations',
                                model = IconLocation,
                                checkrequired = True,
                                version_id_col='version_id',  # optimistic concurrency control
                                idSrc = 'rowid',
                                rule = '/<interest>/iconlocations',
                                endpoint = 'admin.iconlocations',
                                endpointvalues = {'interest':'<interest>'},
                                dbmapping = iconlocation_dbmapping,
                                formmapping = iconlocation_formmapping,
                                validate=location_validate,
                                buttons = ['create', 'edit', 'remove'],
                                clientcolumns =  [
                            { 'name': 'locname', 'data': 'locname', 'label': 'Name',
                              'className': 'field_req',
                              },
                            { 'name': 'icon', 'data': 'icon', 'label': 'Icon',
                              'className': 'field_req',
                              '_treatment' : { 'relationship' : { 'fieldmodel':Icon, 'labelfield':'icon',
                                                                  'formfield':'icon', 'dbfield':'icon',
                                                                  'uselist':False, 'searchbox': True } },
                              },
                           {'name': 'iconsubtype', 'data': 'iconsubtype', 'label': 'Icon Subtype',
                            '_treatment': {'relationship': {'fieldmodel': IconSubtype, 'labelfield': 'iconsubtype',
                                                            'formfield': 'iconsubtype', 'dbfield': 'iconsubtype',
                                                            'uselist': False, 'searchbox': True,
                                                            'nullable': True}},
                            },
                           {'name': 'location', 'data': 'location', 'label': 'Location',
                            'className': 'field_req',
                            'fieldInfo': 'location used for map placement, must work on google maps',
                            },
                           {'name': 'location_popup_text', 'data': 'location_popup_text', 'label': 'Loc Popup Text',
                            'fieldInfo': 'location displayed in pop-up',
                            },
                           {'name': 'contact_name', 'data': 'contact_name', 'label': 'Contact Name',
                            },
                           {'name': 'email', 'data': 'email', 'label': 'Contact Email',
                            },
                           {'name': 'phone', 'data': 'phone', 'label': 'Contact Phone',
                            },
                       ]);
iconlocation.register()

