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
#from utils import render_template


hooks = hookenv.Hooks()


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


def chownr(path, owner, group):
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(group).gr_gid
    for root, dirs, files in os.walk(path):
        for momo in dirs:
            os.chown(os.path.join(root, momo), uid, gid)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)


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


@hooks.hook()
def install():
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    log("Installing required packages", DEBUG)
    apt_install(packages=filter_installed_packages(PACKAGES), fatal=True)
    host.adduser('vcap')
    dirs = [RUN_DIR, LOG_DIR]
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    chownr('/var/vcap', owner='vcap', group='vcap')
    chownr(CF_DIR, owner='vcap', group='vcap')
    log("Stopping Tomcat ...", DEBUG)
    host.service_stop('tomcat7')
    #run(["/etc/init.d/tomcat7", "stop"])
    os.chdir(os.path.join(TOMCAT_HOME, 'lib'))
    log('Installing SQLite jdbc driver jar into Tomcat lib directory', DEBUG)
    run(['wget', 'https://bitbucket.org/xerial/sqlite-jdbc/downloads/'
        'sqlite-jdbc-3.7.2.jar'])
    #log("Cleaning up old config files", DEBUG)
    #execute("rm -rf /var/lib/cloudfoundry/cfuaa/jobs/config/*")


@hooks.hook("config-changed")
def config_changed():
    pass
    #port_config_changed('uaa_port')
    #if emit_uaaconf() and host.service_running('cf-uaa'):
    #    #TODO replace with config reload
    #    host.service_restart('cf-uaa')


@hooks.hook()
def start():
    pass
    #if 'config_ok' in local_state:
    #    if not host.service_running('cf-uaa'):
    #        #hookenv.open_port(local_state['router_port'])
    #        log("Starting UAA as upstart job")
    #        host.service_start('cf-uaa')


@hooks.hook()
def stop():
    pass
    #if host.service_running('cf-uaa'):
    #    host.service_stop('cf-uaa')
    #     hookenv.close_port(local_state['uaa_port'])


#################### Global variables ####################
PACKAGES = ['cfuaa', 'cfuaajob', 'cfregistrar']
CF_DIR = '/var/lib/cloudfoundry'
RUN_DIR = '/var/vcap/sys/run/uaa'
LOG_DIR = '/var/vcap/sys/log/uaa'
CONFIG_FILE = os.path.join(CF_DIR, 'jobs/uaa/config/uaa.yml')
TOMCAT_HOME = '/var/lib/cloudfoundry/cfuaa/tomcat'
SQLITE_JDBC_LIBRARY = 'sqlite-jdbc-3.7.2.jar'
config_data = hookenv.config()
hook_name = os.path.basename(sys.argv[0])
local_state = State('local_state.pickle')
#################### Global variables ####################


if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
