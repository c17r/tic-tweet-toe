from datetime import datetime
from fabric.api import task, env, settings, cd, sudo, run, local, put, path

stamp = datetime.now().strftime("v%Y%m%d%H%M%S")
stamptar = "ttt-" + stamp + ".tar"
stampzip = stamptar + ".gz"

env.stamp = stamp
env.stamptar = stamptar
env.stampzip = stampzip

@task
def live():
    env.hosts = [
        "crow.endrun.org"
    ]

@task
def deploy():
    local('find . \( -name "*.pyc" -or -name "*.pyo" -or -name "*py.class" \) -delete')

    local('tar cf %(stamptar)s requirements/' % env)
    local('tar rf %(stamptar)s tic_tweet_toe/' % env)
    local('tar rf %(stamptar)s run.sh' % env)
    local('tar rf %(stamptar)s tic_tweet_toe.py' % env)
    local('gzip %(stamptar)s' % env)

    put(stampzip, '/tmp/%(stampzip)s' % env)

    local('rm %(stampzip)s' % env)

    with settings(sudo_user='tic_tweet_toe'):

        with cd('/home/tic_tweet_toe/run'):
            sudo('mkdir -p %(stamp)s/src' % env)
            sudo('mkdir -p %(stamp)s/venv' % env)

        with cd('/home/tic_tweet_toe/run/%(stamp)s' % env):
            sudo('tar xfz /tmp/%(stampzip)s -C ./src/' % env)

    sudo('rm /tmp/%(stampzip)s' % env)

    with settings(sudo_user='tic_tweet_toe'):

        with cd('/home/tic_tweet_toe/run/%(stamp)s' % env):
            sudo('virtualenv venv' % env)

            with path('./venv/bin', behavior='prepend'):
                sudo('pip install --quiet --no-cache-dir -r ./src/requirements/default.txt' % env)

        with cd('/home/tic_tweet_toe/run/current/src/'):
            sudo('./run.sh stop')

        with cd('/home/tic_tweet_toe/run'):
            sudo('ln -nsf $(basename $(readlink -f current)) previous' % env)
            sudo('ln -nsf %(stamp)s current' % env)

        with cd('/home/tic_tweet_toe/run/current/src/'):
            sudo('./run.sh start')
