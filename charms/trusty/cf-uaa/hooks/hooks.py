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
        log('Installing upstart job:' + x, DEBUG)
        shutil.copy(x, '/etc/init/')


def port_config_changed(port):
    '''Cheks if value of port changed close old port and open a new one'''
    if port in local_state:
        if local_state[port] != config_data[port]:
            hookenv.close_port(local_state[port])
            local_state[port] = config_data[port]
    else:
        local_state.setdefault(port, config_data[port])
    local_state.save()
    hookenv.open_port(config_data[port])


def all_configs_are_rendered():
    local_state['varz_ok'] && local_state['registrar_ok'] && local_state['uaa_ok']

def emit_all_configs():
    emit_registrar_config() && emit_varz_config() && emit_uaa_config()


def emit_config(module_name, config_items, template_config_file, target_config_file):
    config_context = {}
    success = True

    for key in config_items:
        if key in local_state:
            config_context[key] = local_state[key]
        else:
            success = False

    local_state[module_name + '_ok'] = success
    local_state.save

    if success:
        log('Emited %s config successfully.' % module_name)
        with open(target_config_file, 'w') as config_file:
            config_file.write(render_template(template_config_file, config_context))
    else:
        log('Emit %s conf unsuccessfull' % module_name, WARNING)

    return success    

def emit_registrar_config():
    required_config_items = ['nats_user', 'nats_password', 'nats_address',
                                'nats_port', 'varz_user', 'varz_password']
    emit_config('registrar', required_config_items, 
                'registrar.yml', REGISTRAR_CONFIG_FILE)


def emit_varz_config():
    required_config_items = ['varz_password', 'varz_user']
    emit_config('varz', required_config_items, 
                'varz.yml', VARZ_CONFIG_FILE)


def emit_uaa_config():
    required_config_items = ['varz_password', 'varz_user']
    emit_config('uaa', [], 
                'uaa.yml', UAA_CONFIG_FILE)


@hooks.hook()
def install():
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    log("Installing required packages", DEBUG)
    apt_install(packages=filter_installed_packages(PACKAGES), fatal=True)
    host.adduser('vcap')
    install_upstart_scripts()
    if os.path.isfile('/etc/init.d/tomcat7'):
        run(['update-rc.d', '-f', 'tomcat7', 'remove'])
        log("Stopping Tomcat ...", DEBUG)
        host.service_stop('tomcat7')
        os.remove('/etc/init.d/tomcat7')
    dirs = [RUN_DIR, LOG_DIR, '/var/vcap/jobs/uaa']
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    if not os.path.isfile(os.path.join(TOMCAT_HOME,
                          'lib', 'sqlite-jdbc-3.7.2.jar')):
        os.chdir(os.path.join(TOMCAT_HOME, 'lib'))
        log('Installing SQLite jdbc driver jar into Tomcat lib directory',
            DEBUG)
        #TODO consider installing from charm
        run(['wget', 'https://bitbucket.org/xerial/sqlite-jdbc/downloads/'
            'sqlite-jdbc-3.7.2.jar'])
    log("Cleaning up old config files", DEBUG)
    shutil.rmtree(CONFIG_PATH)
    shutil.copytree(os.path.join(hookenv.charm_dir(),
                    'files/config'), CONFIG_PATH)
    host.mkdir('var/vcap/jobs/uaa', owner='vcap', group='vcap', perms=0775)
    os.chdir('var/vcap/jobs/uaa')
    os.symlink('/var/lib/cloudfoundry/cfuaa/jobs/config',
               'config')
    chownr('/var/vcap', owner='vcap', group='vcap')
    chownr(CF_DIR, owner='vcap', group='vcap')


@hooks.hook("config-changed")
def config_changed():
    local_state['varz_ok']      = False
    local_state['registrar_ok'] = False
    local_state['uaa_ok']       = False
    local_state.save()
    #port_config_changed('uaa_port')
    config_items = ['nats_user', 'nats_password', 'nats_port',
                    'nats_address', 'varz_user', 'varz_password']
    for item in config_items:
        if item in config_data:
            local_state[item] = config_data[item]

    if emit_all_configs()
        # TODO replace with config reload
        # host.service_restart('cf-uaa')
        # host.service_restart('cf-registrar')
        stop()
        start()


@hooks.hook()
def start():
    log("UAA: Start hook is called.")
    if all_configs_are_rendered()
        log("UAA: Start hook: all configs are rendered.")
        if !host.service_running('cf-uaa') 
            log("Starting UAA as upstart job")
            host.service_start('cf-uaa')
        if !host.service_running('cf-registrar'):
            log("Starting cf registrar as upstart job")
            host.service_start('cf-registrar')
    else: 
        log("UAA: Start hook: NOT all configs are rendered.")



@hooks.hook()
def stop():
    if host.service_running('cf-uaa'):
        host.service_stop('cf-uaa')
    if host.service_running('cf-registrar'):
        host.service_stop('cf-registrar')        
    #     hookenv.close_port(local_state['uaa_port'])

@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    log("UAA: nats-relation-changed >>> (attempt to add NATS) ")
    config_changed()
    
    # for relid in hookenv.relation_ids('nats'):
    #     # TODO add checks of values
    #     # TODO run only if values are changed
    #     for key in ['nats_address', 'nats_port', 'nats_user', 'nats_password']:
    #         log(("%s = %s" % key, hookenv.relation_get(key)), DEBUG)
    #         local_state[key] = hookenv.relation_get(key)
    #     local_state.save()
    
    # if emit_all_configs():
    #     stop()
    #     start()


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    # TODO: determine how to notify user and what to do
    log("UAA: nats_relation_broken.")
    config_changed() # will only stop if someone will be missing


@hooks.hook('uaa-relation-joined')
def uaa_relation_joined():
    log('UAA: uaa-relation-joined', DEBUG)
    for relid in hookenv.relation_ids('uaa'):
        log('uaa data to send: ' + local_state['uaa_address'], DEBUG)
        hookenv.relation_set(relid, uaa_address=local_state['uaa_address'])


#################### Global variables ####################
PACKAGES = ['cfuaa', 'cfuaajob', 'cfregistrar']
CF_DIR = '/var/lib/cloudfoundry'
RUN_DIR = '/var/vcap/sys/run/uaa'
LOG_DIR = '/var/vcap/sys/log/uaa'
CONFIG_PATH = os.path.join(CF_DIR, 'cfuaa', 'jobs', 'config')
UAA_CONFIG_FILE = os.path.join(CONFIG_PATH, 'uaa.yml')
VARZ_CONFIG_FILE = os.path.join(CONFIG_PATH, 'varz.yml')
REGISTRAR_CONFIG_FILE = os.path.join(CF_DIR, 'cfregistrar',
                                             'config', 'config.yml')
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
