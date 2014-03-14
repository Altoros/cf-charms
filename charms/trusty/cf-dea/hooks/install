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

from charmhelpers.fetch import (
    apt_install, apt_update, add_source, filter_installed_packages
)
# from utils import render_template


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
    #deacontext = {}
    #with open(DEA_CONFIG_FILE, 'w') as natsconf:
    #    natsconf.write(render_template('nats.yml', natscontext))
    pass


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
    host.adduser('vcap')
    dirs = [DEA_DIR]
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    #install_upstart_scripts()


@hooks.hook()
def start():
    log("Starting DEA as upstart job")
    #host.service_start('cf-dea')


@hooks.hook("config-changed")
def config_changed():
    pass


@hooks.hook()
def stop():
    host.service_stop('cf-dea')
    #hookenv.close_port(local_state['nats_port'])


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    for relid in hookenv.relation_ids('nats'):
        log('NATS address:' + local_state['nats_address'] + ':'
            + str(local_state['nats_port']), DEBUG)
        log('NATS user:' + local_state['nats_user'] + ':'
            + str(local_state['nats_password']), DEBUG)
        hookenv.relation_set(relid,
                             nats_address=local_state['nats_address'],
                             nats_port=local_state['nats_port'],
                             nats_user=local_state['nats_user'],
                             nats_password=local_state['nats_password'],
                             )


@hooks.hook('nats-relation-joined')
def nats_relation_joined():
    log('Hi from joined hook')


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    log('Hi from broken hook')


#################### Global variables ####################
config_data = hookenv.config()
hook_name = os.path.basename(sys.argv[0])
#TODO replace with actual dea package
DEA_PACKAGES = ['git', 'ruby1.9.1-dev', 'libxslt-dev', 'libxml2-dev']

CF_DIR = '/var/lib/cloudfoundry'
DEA_DIR = os.path.join(CF_DIR, 'dea-ng')
local_state = State('local_state.pickle')

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
