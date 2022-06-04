###########################################################################################
# fabfile  -- deployment using Fabric
#
#   Copyright 2019 Lou King
###########################################################################################
'''
fabfile  -- deployment using Fabric
=================================================================

expecting fabric.json with following content
    {
        "connect_kwargs": {
            "key_filename": sshkeyfilename (export OpenSSH key from puttygen)
        },
        "user": "runningroutesmgr"
    }

execute as follows

    fab -H <target-host> deploy

or 

    fab -H <target1>,<target2> deploy

if you need to check out a particular branch

    fab -H <target-host> deploy --branchname=<branch>

'''

from fabric import task
from invoke import Exit

APP_NAME = 'runningroutes'
WSGI_SCRIPT = 'runningroutes.wsgi'

@task
def deploy(c, branchname='master'):
    print('c.user={} c.host={} branchname={}'.format(c.user, c.host, branchname))

    venv_dir = '/var/www/{server}/venv'.format(server=c.host)
    project_dir = '/var/www/{server}/{appname}/{appname}'.format(server=c.host, appname=APP_NAME)

    c.run('cd {} && git pull'.format(project_dir))
    
    if not c.run('cd {} && git show-ref --verify --quiet refs/heads/{}'.format(project_dir, branchname), warn=True):
        raise Exit('branchname {} does not exist'.format(branchname))

    c.run('cd {} && git checkout {}'.format(project_dir, branchname))
    c.run('cd {} && cp -R ../../libs/js  runningroutes/static'.format(project_dir))
    # must source bin/activate before each command which must be done under venv
    # because each is a separate process
    c.run('cd {} && source {}/bin/activate && pip install -r requirements.txt'.format(project_dir, venv_dir))
    
    versions_dir = '{}/migrations/versions'.format(project_dir)
    if not c.run('test -d {}'.format(versions_dir), warn=True):
        c.run('mkdir -p {}'.format(versions_dir))
    
    c.run('cd {} && source {}/bin/activate && flask db upgrade'.format(project_dir, venv_dir))
    c.run('cd {} && touch {}'.format(project_dir, WSGI_SCRIPT))
