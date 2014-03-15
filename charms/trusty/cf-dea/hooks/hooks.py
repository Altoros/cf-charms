#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import pwd
import grp
import sys
import subprocess
import glob
import shutil
import cPickle as pickle

from charmhelpers.core import hookenv, host
from charmhelpers.core.hookenv import log, DEBUG, ERROR, WARNING

from charmhelpers.fetch import (
    apt_install, apt_update, add_source, filter_installed_packages
)
from utils import render_template


hooks = hookenv.Hooks()


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


def install_upstart_scripts():
    for x in glob.glob('files/upstart/*.conf'):
        print 'Installing upstart job:', x
        shutil.copy(x, '/etc/init/')


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


def emit_deaconf():
    deacontext = {}
    success = True
    if 'nats_user' in local_state:
        deacontext.setdefault('nats_user', local_state['nats_user'])
    else:
        success = False
    if 'nats_password' in local_state:
        deacontext.setdefault('nats_password', local_state['nats_password'])
    else:
        success = False
    if 'nats_port' in local_state:
        deacontext.setdefault('nats_port', local_state['nats_port'])
    else:
        success = False
    if 'nats_address' in local_state:
        deacontext.setdefault('nats_address', local_state['nats_address'])
    else:
        success = False
    if success:
        log('Emit dea conf successfull')
        with open(DEA_CONFIG_PATH, 'w') as deaconf:
            deaconf.write(render_template('dea.yml', deacontext))
        local_state['config_ok'] = 'true'
        return True
    else:
        if 'config_ok' in local_state:
            del local_state['config_ok']
            local_state.save()
        log('Emit dea conf unsuccessfull', WARNING)
        return False


def chownr(path, owner, group):
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(group).gr_gid
    for root, dirs, files in os.walk(path):
        for momo in dirs:
            os.chown(os.path.join(root, momo), uid, gid)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)


@hooks.hook()
def install():
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    apt_install(packages=filter_installed_packages(DEA_PACKAGES), fatal=True)
    install_upstart_scripts()
    host.adduser('vcap')
    host.mkdir(CF_DIR, owner='vcap', group='vcap', perms=0775)
    os.chdir(CF_DIR)
    run(['gem', 'install', 'bundle', 'eventmachine'])
    run(['gem', 'install', 'bundle'])
    run(['git', 'clone', 'https://github.com/cloudfoundry/dea_ng.git'])
    dirs = [DEA_PIDS_DIR, DEA_CACHE_DIR, DEA_BP_CACHE_DIR]
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    os.chdir(DEA_DIR)
    run(['git', 'submodule', 'update', '--init'])
    run(['bundle', 'install', '--without', 'test'])
    chownr(CF_DIR, 'vcap', 'vcap')


@hooks.hook()
def start():
    if 'config_ok' in local_state:
        if not host.service_running('cf-dea'):
            #hookenv.open_port(local_state['router_port'])
            log("Starting DEA as upstart job")
            host.service_start('cf-dea')


@hooks.hook("config-changed")
def config_changed():
    #port_config_changed('router_port')
        if emit_deaconf() and host.service_running('cf-dea'):
        #TODO replace with config reload
        host.service_restart('cf-dea')


@hooks.hook()
def stop():
    if host.service_running('cf-dea'):
        host.service_stop('cf-dea')
#        hookenv.close_port(local_state['router_port'])


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    for relid in hookenv.relation_ids('nats'):
        #TODO add checks of values
        local_state['nats_address'] = hookenv.relation_get('nats_address')
        local_state['nats_port'] = hookenv.relation_get('nats_port')
        local_state['nats_user'] = hookenv.relation_get('nats_user')
        local_state['nats_password'] = hookenv.relation_get('nats_password')
        local_state.save()
    if emit_deaconf():
        start()


@hooks.hook('nats-relation-departed')
def nats_relation_departed():
    log('Hi from departed hook')


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    stop()


#################### Global variables ####################
config_data = hookenv.config()
hook_name = os.path.basename(sys.argv[0])
#TODO replace with actual dea package
DEA_PACKAGES = ['g++', 'make', 'git', 'ruby1.9.1-dev', 'libxslt-dev',
                'libxml2-dev']

CF_DIR = '/var/lib/cloudfoundry'
DEA_DIR = os.path.join(CF_DIR, 'dea_ng')
DEA_PIDS_DIR = os.path.join(DEA_DIR, 'pids')
DEA_CACHE_DIR = os.path.join(DEA_DIR, 'cache')
DEA_BP_CACHE_DIR = os.path.join(DEA_DIR, 'buildpack_cache')
DEA_CONFIG_PATH = os.path.join(DEA_DIR, 'config', 'dea.yml')
local_state = State('local_state.pickle')

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
