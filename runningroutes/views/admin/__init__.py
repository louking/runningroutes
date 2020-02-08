###########################################################################################
# blueprint for this view folder
#
#       Date            Author          Reason
#       ----            ------          ------
#       12/03/19        Lou King        Create
#
#   Copyright 2019 Lou King
###########################################################################################

from flask import Blueprint

bp = Blueprint('admin', __name__.split('.')[0], url_prefix='/admin', static_folder='static/admin', template_folder='templates/admin')

# import views
from . import login
from . import userrole
from . import routes
from . import icons
from . import files
from . import sysinfo
