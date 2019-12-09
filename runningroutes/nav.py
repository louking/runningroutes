###########################################################################################
# nav - navigation 
#
#       Date            Author          Reason
#       ----            ------          ------
#       07/06/18        Lou King        Create (from https://raw.githubusercontent.com/louking/rrwebapp/master/rrwebapp/nav.py)
#
#   Copyright 2018 Lou King.  All rights reserved
#
###########################################################################################
'''
nav - navigation
======================
define navigation bar based on privileges
'''

# standard

# pypi
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup
from flask_nav.renderers import SimpleRenderer
from dominate import tags
from flask_security import current_user
from flask import current_app

thisnav = Nav()

@thisnav.renderer()
class NavRenderer(SimpleRenderer):
    def visit_Subgroup(self, node):
        group = tags.ul(_class='subgroup')
        title = tags.div(node.title)

        if node.active:
            title.attributes['class'] = 'active'

        for item in node.items:
            group.add(tags.li(self.visit(item)))

        return [title, group]

@thisnav.navigation()
def nav_menu():
    navbar = Navbar('nav_menu')

    navbar.items.append(View('Home', 'admin'))

    # event administrative stuff
    if current_user.has_role('event-admin') or current_user.has_role('super-admin'):
        pass



    # sponsor stuff
    if current_user.has_role('sponsor-admin') or current_user.has_role('super-admin'):
        pass

    if current_user.has_role('event-admin') or current_user.has_role('sponsor-admin') or current_user.has_role('super-admin'):
        pass

    # superadmin stuff
    if current_user.has_role('super-admin'):
        userroles = Subgroup('User/Roles')
        navbar.items.append(userroles)
        userroles.items.append(View('Users', 'admin.users'))
        userroles.items.append(View('Roles', 'admin.roles'))
        userroles.items.append(View('Interests', 'admin.interests'))

        navbar.items.append(View('Debug', 'admin.debug'))

    # finally for non super-admin
    else:
        navbar.items.append(View('About', 'admin.sysinfo'))

    return navbar

thisnav.init_app(current_app)
