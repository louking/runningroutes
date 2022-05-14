'''
nav - navigation
======================
define navigation bar based on privileges
'''

# standard

# pypi
from flask import g, current_app
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup
from flask_nav.renderers import SimpleRenderer
from dominate import tags
from flask_security import current_user

# homegrown
from .models import ROLE_SUPER_ADMIN, ROLE_ROUTES_ADMIN, ROLE_ICON_ADMIN

thisnav = Nav()

@thisnav.renderer()
class NavRenderer(SimpleRenderer):
    def visit_Subgroup(self, node):
        # 'a' tag required by smartmenus
        title = tags.a(node.title, href="#")
        group = tags.ul(_class='subgroup')

        if node.active:
            title.attributes['class'] = 'active'

        for item in node.items:
            group.add(tags.li(self.visit(item)))

        return [title, group]

@thisnav.navigation()
def nav_menu():
    navbar = Navbar('nav_menu')

    if current_user.is_authenticated:
        navbar.items.append(View('Home', 'admin.home', interest=g.interest))
        # deeper functions are only accessible when interest is set
        if g.interest:
            if current_user.has_role(ROLE_ROUTES_ADMIN) or current_user.has_role(ROLE_SUPER_ADMIN):
                navbar.items.append(View('Edit Routes', 'admin.routetable', interest=g.interest))

            if current_user.has_role(ROLE_ICON_ADMIN) or current_user.has_role(ROLE_SUPER_ADMIN):
                icons = Subgroup('Icons')
                navbar.items.append(icons)
                icons.items.append(View('Icon Locations', 'admin.iconlocations', interest=g.interest))
                icons.items.append(View('Icon Map', 'admin.iconmap', interest=g.interest))
                icons.items.append(View('Icons', 'admin.icons', interest=g.interest))
                icons.items.append(View('Icon Subtypes', 'admin.iconsubtypes', interest=g.interest))

        # superadmin stuff
        if current_user.has_role(ROLE_SUPER_ADMIN):
            super = Subgroup('Super')
            navbar.items.append(super)
            super.items.append(View('Users', 'userrole.users'))
            super.items.append(View('Roles', 'userrole.roles'))
            # this doesn't work because https://github.com/jwag956/flask-security/blob/743be9c979b558b4ecfb177dc8117c0bf55e38ed/flask_security/views.py#L464
            # requires forgot_password has anonymous_user_required decorator
            # super.items.append(View('Reset PW', 'security.forgot_password'))
            super.items.append(View('Interests', 'userrole.interests'))
            super.items.append(View('Files', 'admin.files'))
            super.items.append(View('Debug', 'admin.debug'))

        # all authenticated users get these common items
        navbar.items.append(View('My Account', 'security.change_password'))
        if g.interest:
            navbar.items.append(View('User View', 'frontend.routes', interest=g.interest))
        navbar.items.append(View('About', 'admin.sysinfo'))

    return navbar

thisnav.init_app(current_app)
