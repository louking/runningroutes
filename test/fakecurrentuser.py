'''
fakecurrentuser - minimal stand-in for flask_security.current_user, for tests

Several view modules (nav.py, views/admin/routes.py, views/admin/icons.py,
views/frontend/frontend.py) call current_user.is_authenticated/.has_role(role)/.roles/.interests
directly rather than taking a user as a parameter, and each module imports its own `current_user`
name (`from flask_security import current_user`) -- so tests monkeypatch that module-level name
to one of these rather than setting up real Flask-Security login state.
'''


class FakeCurrentUser:
    def __init__(self, roles=(), interests=(), is_authenticated=True):
        self.roles = list(roles)
        self.interests = list(interests)
        self.is_authenticated = is_authenticated

    def has_role(self, role):
        return role in self.roles
