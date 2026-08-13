'''
test_dbinit - test runningroutes.dbinit
=========================================================
'''

# homegrown
from runningroutes.dbinit import init_db
from loutilities.user.model import Role, User, Interest


def test_init_db_creates_roles(dbapp):
    init_db(defineowner=False)

    rolenames = {r.name for r in Role.query.all()}
    assert rolenames == {'super-admin', 'interest-admin'}


def test_init_db_creates_interests(dbapp):
    init_db(defineowner=False)

    interests = {i.interest: i.public for i in Interest.query.all()}
    assert interests == {'fsrc': True, 'l-and-h': False}


def test_init_db_without_defineowner_creates_no_user(dbapp):
    init_db(defineowner=False)

    assert User.query.count() == 0


def test_init_db_defineowner_creates_owner_with_roles_and_interests(dbapp):
    init_db(defineowner=True)

    owner = User.query.filter_by(email=dbapp.config['APP_OWNER']).one()
    assert owner.name == dbapp.config['APP_OWNER_NAME']
    assert {r.name for r in owner.roles} == {'super-admin', 'interest-admin'}
    assert {i.interest for i in owner.interests} == {'fsrc', 'l-and-h'}


def test_init_db_defineowner_idempotent(dbapp):
    init_db(defineowner=True)
    init_db(defineowner=True)

    assert User.query.filter_by(email=dbapp.config['APP_OWNER']).count() == 1
