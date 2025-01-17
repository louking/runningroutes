'''
fabfile  -- deployment using Fabric
=================================================================

expecting fabric.json with following content
    {
        "connect_kwargs": {
            "key_filename": sshkeyfilename (export OpenSSH key from puttygen)
        },
        "user": "appuser"
    }

execute as follows

    fab -H <target-host> deploy [prod, sandbox

or 

    fab -H <target1>,<target2> deploy [prod, sandbox]

if you need to check out a particular branch

    fab -H <target-host> deploy --branchname=<branch>

'''

from fabric import task
from invoke import Exit

APP_NAME = 'routes'
PROJECT_NAME = 'runningroutes'

qualifiers = ['prod', 'sandbox']

@task
def deploy(c, qualifier, branchname='master'):
    if qualifier not in qualifiers:
        raise Exit(f'deploy qualifier parameter must be one of {qualifiers}')
        
    print(f'c.user={c.user} c.host={c.host} branchname={branchname}')

    project_dir = f'~/{APP_NAME}-{qualifier}'

    for the_file in ['docker-compose.yml']:
        if not c.run(f"cd {project_dir} && curl --fail -O 'https://raw.githubusercontent.com/louking/{PROJECT_NAME}/{branchname}/{the_file}'", warn=True):
            raise Exit(f'louking/{PROJECT_NAME}/{branchname}/{the_file} does not exist')

    # stop and build/start docker services
    c.run(f'cd {project_dir} && docker compose pull')
    c.run(f'cd {project_dir} && docker compose up -d')
