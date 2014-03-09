#!/usr/bin/env python
# vim: et sta sts ai ts=4 sw=4:

import os
import sys
import time
import glob
import subprocess
import shutil
from cloudfoundry import ROUTER_PACKAGES
from charmhelpers.core import hookenv, host
from charmhelpers.payload.execd import execd_preinstall

config_data = hookenv.config()

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG,
    )

from charmhelpers.fetch import (
    apt_install,
    apt_update,
    filter_installed_packages,
    add_source
)
from utils import render_template
from cloudfoundry import chownr

ROUTER_PATH = '/var/lib/cloudfoundry/cfgorouter'
CF_DIR = '/var/lib/cloudfoundry'


def Template(*args, **kw):
    """jinja2.Template with deferred jinja2 import.

    jinja2 may not be importable until the install hook has installed the
    required packages.
    """
    from jinja2 import Template
    return Template(*args, **kw)

hooks = hookenv.Hooks()


def install_upstart_scripts():
    for x in glob.glob('files/upstart/*.conf'):
        print 'Installing upstart job:', x
        shutil.copy(x, '/etc/init/')


def log(msg, lvl=INFO):
    myname = hookenv.local_unit().replace('/', '-')
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    with open('{}/{}-debug.log'.format(juju_log_dir, myname), 'a') as f:
        f.write('{} {}: {}\n'.format(ts, lvl, msg))
    hookenv.log(msg, lvl)


def run(command, exit_on_error=True, quiet=False):
    '''Run a command and return the output.'''
    if not quiet:
        log("Running {!r}".format(command), DEBUG)
    p = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        shell=isinstance(command, basestring))
    p.stdin.close()
    lines = []
    for line in p.stdout:
        if line:
            # LP:1274460 & LP:1259490 mean juju-log is no where near as
            # useful as we would like, so just shove a copy of the
            # output to stdout for logging.
            # log("> {}".format(line), DEBUG)
            if not quiet:
                print line
            lines.append(line)
        elif p.poll() is not None:
            break

    p.wait()

    if p.returncode == 0:
        return '\n'.join(lines)

    if p.returncode != 0 and exit_on_error:
        log("ERROR: {}".format(p.returncode), ERROR)
        sys.exit(p.returncode)

    raise subprocess.CalledProcessError(
        p.returncode, command, '\n'.join(lines))


def emit_routerconf():
    routercontext = {
        'nats_ip': config_data['nats_address'],
        'nats_port': config_data['nats_port'],
        'router_port': config_data['router_port'],
    }
    with open('/var/lib/cloudfoundry/config/gorouter.yml', 'w') as routerconf:
        routerconf.write(render_template('gorouter.yml', routercontext))

hooks = hookenv.Hooks()


@hooks.hook()
def install():
    execd_preinstall()
    #add_source(config_data['source'], config_data['key'])
    #apt_update(fatal=True)
    apt_install(packages=ROUTER_PACKAGES, fatal=True)
    host.adduser('vcap')
    dirs = [CF_DIR + '/src/github.com/cloudfoundry', CF_DIR + '/config',
            CF_DIR + '/src/github.com/stretchr',
            '/var/vcap/sys/run/gorouter', '/var/vcap/sys/log/gorouter']
    for dir in dirs:
        host.mkdir(dir, owner='vcap', group='vcap', perms=0775)
    emit_routerconf()
    install_upstart_scripts()
    os.chdir(CF_DIR)
    os.environ['GOPATH'] = CF_DIR
    os.environ["PATH"] = CF_DIR + os.pathsep + os.environ["PATH"]
    os.chdir(CF_DIR + '/src/github.com/cloudfoundry')
    run(['git', 'clone', 'https://github.com/cloudfoundry/gorouter.git'])
    os.chdir(CF_DIR + '/src/github.com/stretchr/')
    run(['git', 'clone', 'https://github.com/stretchr/objx.git'])
    os.chdir(CF_DIR)
    run(['go', 'get', '-v', './src/github.com/cloudfoundry/gorouter/...'])
    run(['go', 'get', '-v', './...'])
    run(['go', 'build', '-v', './...'])
    chownr('/var/lib/cloudfoundry', owner='vcap', group='vcap')
    chownr('/var/vcap', owner='vcap', group='vcap')


@hooks.hook()
def start():
    log("Starting router daemonized in the background")
    host.service_start('gorouter')


@hooks.hook("config-changed")
def config_changed():
    hookenv.open_port(config_data['router_port'])


@hooks.hook()
def stop():
    host.service_stop('gorouter')
    hookenv.close_port(config_data['router_port'])


@hooks.hook('db-relation-changed')
def cc_relation_changed():
    pass


hook_name = os.path.basename(sys.argv[0])
juju_log_dir = "/var/log/juju"

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
