import os

import pytest
from flask import Flask

# APP_NAME/APP_VER are normally supplied by Docker Compose's .env; set them here so the
# runningroutes package (which reads os.environ['APP_NAME'] at import time) also works for
# local/CI pytest runs
os.environ.setdefault('APP_NAME', 'runningroutes')
os.environ.setdefault('APP_VER', '0.0.0')

from runningroutes import create_app
from runningroutes.models import db
from runningroutes.settings import Testing
from loutilities.user.model import Application


def _create_all():
    for bind_key, metadata in db.metadatas.items():
        engine = db.engines[bind_key]
        metadata.create_all(bind=engine)


def _drop_all():
    for bind_key, metadata in db.metadatas.items():
        engine = db.engines[bind_key]
        metadata.drop_all(bind=engine)


def _rebind_session(bound_app):
    '''(re)point db.session at bound_app's own engines

    create_app() (runningroutes/__init__.py) replaces Flask-SQLAlchemy's normal per-app
    db.session proxy with a single scoped_session hardwired to whichever app's engines were
    active when it ran: `db.session = scoped_session(sessionmaker(binds=db.get_binds()))`. Since
    that db.session object is a plain module-global on the shared `db = SQLAlchemy()` instance
    (not re-resolved per current_app), it silently keeps pointing at the *first* app it was bound
    to for the rest of the process -- so interleaving the real (session-scoped) `app` fixture with
    the lightweight `bareapp`/`bare_dbapp` fixtures across different tests would otherwise leave
    later tests querying through a session bound to the wrong app's engines entirely (tables
    created in one sqlite file, queries executed against a session pointed at a different one).
    Every fixture that hands out a app/dbapp-style object calls this to repoint db.session at its
    own engines every time, regardless of what ran before it.
    '''
    from sqlalchemy.orm import scoped_session, sessionmaker
    with bound_app.app_context():
        db.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, binds=db.get_binds()))


@pytest.fixture(scope='session')
def _dburis(tmp_path_factory):
    '''file-based (not :memory:) sqlite paths shared by every fixture in the session

    file-based sqlite avoids a :memory: multi-bind flush/commit visibility gotcha found while
    testing update_local_tables() in the members repo (see that repo's CLAUDE.md) -- using file
    databases here from the start sidesteps that whole class of problem.
    '''
    d = tmp_path_factory.mktemp('db')
    return {
        'default': 'sqlite:///{}'.format(d / 'app.db'),
        'users': 'sqlite:///{}'.format(d / 'users.db'),
    }


@pytest.fixture(scope='session')
def app(_dburis):
    '''Real app built via create_app(), constructed exactly ONCE per test session.

    locations.py, views/admin/routes.py, views/admin/icons.py, views/frontend/frontend.py, and
    views/frontend/icons.py all do a module-scope `from . import app` / `Client(key=app.config[...])`
    -- these run as a side effect of create_app() registering the admin/frontend blueprints, and
    Python only executes a module body on its *first* import. A second create_app() call would
    build a second Flask app/config, but those already-imported modules would stay bound to the
    first call's app/gmaps client forever. So build the real app once per session here, and reset
    the database between tests (see dbapp) instead of calling create_app() again.

    create_app() unconditionally queries the Application table (for g.loutility) while creating
    the app (runningroutes/__init__.py), before any table exists -- so a bare Flask app pointed at
    the same (file-based) database is used to create tables and seed that Application row first.
    '''
    class _SessionTesting(Testing):
        SQLALCHEMY_DATABASE_URI = _dburis['default']
        SQLALCHEMY_BINDS = {'users': _dburis['users']}

    bootstrap = Flask('runningroutes-test-bootstrap')
    bootstrap.config['SQLALCHEMY_DATABASE_URI'] = _dburis['default']
    bootstrap.config['SQLALCHEMY_BINDS'] = {'users': _dburis['users']}
    bootstrap.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(bootstrap)
    with bootstrap.app_context():
        _create_all()
        db.session.add(Application(application=_SessionTesting.APP_LOUTILITY))
        db.session.commit()

    real_app = create_app(_SessionTesting, init_for_operation=False)
    yield real_app


# executed prior to each test: reset every table to empty, and reseed the Application row
# create_app()'s before_request handler (g.loutility) depends on
@pytest.fixture
def dbapp(app):
    _rebind_session(app)
    with app.app_context():
        _drop_all()
        _create_all()
        db.session.add(Application(application=app.config['APP_LOUTILITY']))
        db.session.commit()
        yield app


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


# deliberately NOT using create_app(): besides the g.loutility-before-create_all ordering issue
# (see the app fixture above), a bare Flask app is enough for model/free-function-level tests that
# don't need the full app (routing, security, mail, gmaps-client-bearing view modules) -- see
# test_helpers.py, test_models.py
@pytest.fixture
def bareapp(tmp_path):
    '''Minimal Flask app with runningroutes' db bound, no blueprints/extensions registered.

    Uses file-based (not :memory:) sqlite -- see the members repo's CLAUDE.md for a documented
    :memory:-plus-cross-bind-query visibility gotcha found testing update_local_tables() there
    (a row added and only flushed on one bind isn't reliably visible after a query on the
    *other* bind intervenes). File-based sqlite doesn't have that failure mode, so it's used
    everywhere here from the start rather than adding a separate fixture just for
    update_local_tables() tests.
    '''
    bareapp = Flask('runningroutes')
    bareapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(tmp_path / 'bare-app.db')
    # loutilities.user.model.Application/Interest/User/Role share runningroutes' db object via the
    # 'users' bind
    bareapp.config['SQLALCHEMY_BINDS'] = {'users': 'sqlite:///{}'.format(tmp_path / 'bare-users.db')}
    bareapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    bareapp.config['TESTING'] = True
    db.init_app(bareapp)
    _rebind_session(bareapp)
    yield bareapp


@pytest.fixture
def bare_dbapp(bareapp):
    '''bareapp fixture with a fresh in-memory database created for the test.'''
    with bareapp.app_context():
        _drop_all()
        _create_all()
        yield bareapp
