###########################################################################################
# env -- alembic environment
#
#   Date        Author      Reason
#   ----        ------      ------
#   01/08/20    Lou King    Create
#
#   Copyright 2020 Lou King
###########################################################################################

# standard

from configparser import ConfigParser
from logging.config import fileConfig

# pypi
from alembic import context
from sqlalchemy import engine_from_config, pool

# make sure this package is available
# see https://stackoverflow.com/questions/16076480/alembic-env-py-target-metadata-metadata-no-module-name-al-test-models
import os, sys
sys.path.append(os.getcwd())

# homegrown
from runningroutes.models import db

# build database name, details kept in apikey database
# get configuration
thisdir = os.path.dirname(__file__)
sep = os.path.sep
configdir = sep.join(thisdir.split(sep)[:-2] + ['config'])
configpath = os.path.join(configdir, 'runningroutes.cfg')
config = ConfigParser()
config.read_file(open(configpath))

# not sure why we need eval here to get rid of quotes, but not in the main application
dbuser = eval(config.get('database', 'dbuser'))
password = eval(config.get('database', 'dbpassword'))
dbserver = eval(config.get('database', 'dbserver'))
dbname = eval(config.get('database', 'dbname'))
db_uri = 'mysql://{uname}:{pw}@{server}/{dbname}'.format(uname=dbuser,pw=password,server=dbserver,dbname=dbname)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Overwrite the sqlalchemy.url in the alembic.ini file.
# config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
# configpath = os.path.join(os.path.sep.join(os.getcwd().split(os.path.sep)[:-2]), 'rrwebapp.cfg')
# print 'os.getcwd()="{}", configpath="{}"'.format(os.getcwd(),configpath)
# appconfig = getitems(configpath, 'app')
config.set_main_option('sqlalchemy.url', db_uri)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    # http://blog.code4hire.com/2017/06/setting-up-alembic-to-detect-the-column-length-change/
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
