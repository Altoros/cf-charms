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
import cPickle as pickle

from helpers.config_helper import find_config_parameter, emit_config
from helpers.upstart_helper import install_upstart_scripts

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG, log,
    )
from charmhelpers.fetch import (
    apt_install,
    apt_update,
    filter_installed_packages,
    add_source
)
from utils import render_template
from cloudfoundry import chownr


class State(dict):
    """Encapsulate state common to the unit for republishing to relations."""
    def __init__(self, state_file):
        super(State, self).__init__()
        self._state_file = state_file
        self.load()

    def load(self):
        '''Load stored state from local disk.'''
        if os.path.exists(self._state_file):
            state = pickle.load(open(self._state_file, 'rb'))
        else:
            state = {}
        self.clear()

        self.update(state)

    def save(self):
        '''Store state to local disk.'''
        state = {}
        state.update(self)
        pickle.dump(state, open(self._state_file, 'wb'))


def Template(*args, **kw):
    """jinja2.Template with deferred jinja2 import.

    jinja2 may not be importable until the install hook has installed the
    required packages.
    """
    from jinja2 import Template
    return Template(*args, **kw)



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


def emit_router_config():

    config_items = ['nats_user', 'nats_password', 'nats_port', 'nats_address', 'router_port',
                    'router_status_port', 'router_status_user', 'router_status_password']

    emit_config('router', config_items, local_state,
                'gorouter.yml', ROUTER_CONFIG_FILE)



hooks = hookenv.Hooks()


@hooks.hook()
def install():
    execd_preinstall()
    apt_install(packages=ROUTER_PACKAGES, fatal=True)
    host.adduser('vcap')
    dirs = [CF_DIR + '/src/github.com/cloudfoundry', CF_DIR + '/config',
            CF_DIR + '/src/github.com/stretchr',
            '/var/vcap/sys/run/gorouter', '/var/vcap/sys/log/gorouter']
    for dir in dirs:
        host.mkdir(dir, owner='vcap', group='vcap', perms=0775)

    install_upstart_scripts()
    os.chdir(CF_DIR)
    os.environ['GOPATH'] = CF_DIR
    os.environ["PATH"] = CF_DIR + os.pathsep + os.environ["PATH"]
    #ToDo: git clone is nor idempotent. If repo dir exists it exits with error
    #fix it by deleting 'src' directory before. This won't allow to redeploy to an existing machine
    os.chdir(CF_DIR + '/src/github.com/cloudfoundry')
    # TODO: check if repo already exists
    # CAUSES ERROR fatal: destination path 'gorouter' already exists and is not an empty directory.
    run(['git', 'clone', 'https://github.com/cloudfoundry/gorouter.git'])
    os.chdir(CF_DIR + '/src/github.com/stretchr/')
    run(['git', 'clone', 'https://github.com/stretchr/objx.git'])
    os.chdir(CF_DIR)
    run(['go', 'get', '-v', './src/github.com/cloudfoundry/gorouter/...'])
    run(['go', 'get', '-v', './...'])
    run(['go', 'build', '-v', './...'])
    os.chdir(hookenv.charm_dir())
    chownr('/var/lib/cloudfoundry', owner='vcap', group='vcap')
    chownr('/var/vcap', owner='vcap', group='vcap')


def port_config_changed(port):
    '''Cheks if value of port changed close old port and open a new one'''
    if port in local_state:
        if local_state[port] != config_data[port]:
            log('Stored value for {} isn\'t equal to config data'.format(port),
                DEBUG)
            log('Closing port {}'.format(str(local_state[port])), WARNING)
            try: 
                hookenv.close_port(local_state[port])
            except:
                log('{} port is not closed.'.format(str(local_state[port])), WARNING)

    hookenv.open_port(config_data[port])
    local_state[port] = config_data[port]
    local_state.save()


@hooks.hook()
def start():
    if local_state['router_ok']:
        if not host.service_running('gorouter'):
            log("Starting router daemonized in the background")
            host.service_start('gorouter')


@hooks.hook("config-changed")
def config_changed():
    local_state['router_ok'] = False

    config_items = ['nats_user', 'nats_password', 'nats_port', 'nats_address', 'router_port',
                    'router_status_port', 'router_status_user', 'router_status_password']
    
    for key in config_items:
        value = find_config_parameter(key, hookenv, config_data)
        log(("%s = %s" % (key, value)), DEBUG)
        local_state[key] = value


    local_state.save()
    port_config_changed('router_port')
    emit_router_config()    

    stop()
    start()

@hooks.hook()
def stop():
    if host.service_running('gorouter'):
        host.service_stop('gorouter')
        hookenv.close_port(local_state['router_port'])


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    config_changed()


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    stop()


@hooks.hook('router-relation-changed')
def router_relation_changed():
    pass


@hooks.hook('router-relation-joined')
def router_relation_joined():
    pass


############################### Global variables ############
ROUTER_PATH = '/var/lib/cloudfoundry/cfgorouter'
CF_DIR = '/var/lib/cloudfoundry'
ROUTER_CONFIG_FILE='/var/lib/cloudfoundry/config/gorouter.yml'
local_state = State('local_state.pickle')
hook_name = os.path.basename(sys.argv[0])
config_data = hookenv.config()


if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
