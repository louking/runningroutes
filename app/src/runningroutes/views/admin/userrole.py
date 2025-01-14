'''
userrole - manage application users and roles
====================================================
'''

# standard

# pypi
from validators.slug import slug
from validators.email import email
from flask_security.recoverable import send_reset_password_instructions
from loutilities.tables import DbCrudApiRolePermissions
from loutilities.tables import get_request_action
from loutilities.user.views.userrole import UserView, InterestView, RoleView
from loutilities.user.roles import ROLE_SUPER_ADMIN

# homegrown
from . import bp
from ... import user_datastore
from ...models import update_local_tables
from ...version import __docversion__

adminguide = f'https://runningroutes.readthedocs.io/en/{__docversion__}/admin-guide.html'

class LocalUserView(UserView):
    def editor_method_postcommit(self, form):
        update_local_tables()
user_view = LocalUserView(
    pagename='users',
    user_datastore=user_datastore,
    roles_accepted=[ROLE_SUPER_ADMIN],
    endpoint='userrole.users',
    rule='/users',
    templateargs={'adminguide': adminguide},
)
user_view.register()

class LocalInterestView(InterestView):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        args = dict(
            templateargs={'adminguide': adminguide},
        )
        args.update(kwargs)

        # initialize inherited class, and a couple of attributes
        super().__init__(**args)

    def editor_method_postcommit(self, form):
        update_local_tables()
interest_view = LocalInterestView()
interest_view.register()

class LocalRoleView(RoleView):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        args = dict(
            templateargs={'adminguide': adminguide},
        )
        args.update(kwargs)

        # initialize inherited class, and a couple of attributes
        super().__init__(**args)

    def editor_method_postcommit(self, form):
        update_local_tables()
role_view = LocalRoleView()
role_view.register()
