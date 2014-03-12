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
from charmhelpers.core.hookenv import log, DEBUG, ERROR
#from charmhelpers.payload.execd import execd_preinstall

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


def emit_natsconf():
    natscontext = {
        'nats_port': config_data['nats_port'],
        'nats_user': config_data['nats_user'],
        'nats_password': config_data['nats_password'],
    }
    log('NATS address:'+config_data['nats_address'], DEBUG)
    if not config_data['nats_address']:
        log('nats_address is empty. using unit\'s IP')
        natscontext['nats_address'] = hookenv.unit_private_ip()
    else:
        natscontext['nats_address'] = config_data['nats_address']
    with open(NATS_CONFIG_FILE, 'w') as natsconf:
        natsconf.write(render_template('nats.yml', natscontext))


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
    apt_install(packages=filter_installed_packages(NATS_PACKAGES), fatal=True)
    host.adduser('vcap')
    dirs = [NATS_RUN_DIR, NATS_LOG_DIR]
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    chownr('/var/vcap', owner='vcap', group='vcap')
    chownr(CF_DIR, owner='vcap', group='vcap')
    install_upstart_scripts()
    emit_natsconf()
    if not 'nats_port' in local_state:
        local_state.setdefault('nats_port', config_data['nats_port'])
        local_state.save()


@hooks.hook()
def start():
    log("Starting NATS as upstart job")
    host.service_start('cf-nats')


@hooks.hook("config-changed")
def config_changed():
    config_data = hookenv.config()
    emit_natsconf()
    if 'nats_port' in local_state:
        if local_state['nats_port'] != config_data['nats_port']:
            log('Nats port in State:' + str(local_state['nats_port']) +
                ', new port:' + str(config_data['nats_port']), DEBUG)
            hookenv.close_port(local_state['nats_port'])
            local_state['nats_port'] = config_data['nats_port']
    else:
        log('nats_port not found in State data', DEBUG)
        local_state.setdefault('nats_port', config_data['nats_port'])
    local_state.save()
    hookenv.open_port(config_data['nats_port'])
    if host.service_running('cf-nats'):
        host.service_restart('cf-nats')


@hooks.hook()
def stop():
    host.service_stop('cf-nats')
    hookenv.close_port(config_data['nats_port'])


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    for relid in hookenv.relation_ids('nats'):
        hookenv.relation_set(relid, nats_address=config_data['nats_address'],
                             nats_port=config_data['nats_port'])


#################### Global variables ####################
config_data = hookenv.config()
hook_name = os.path.basename(sys.argv[0])
#TODO replace with actual nats package
NATS_PACKAGES = ['cfcloudcontroller', 'cfcloudcontrollerjob']

CF_DIR = '/var/lib/cloudfoundry'
NATS_RUN_DIR = '/var/vcap/sys/run/nats'
NATS_LOG_DIR = '/var/vcap/sys/log/nats'
NATS_CONFIG_FILE = os.path.join(CF_DIR,
                                'cfcloudcontroller/jobs/config/nats.yml')
local_state = State('local_state.pickle')

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
