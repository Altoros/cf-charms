#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import subprocess
import glob
import shutil
import pwd
import grp
import cPickle as pickle

from charmhelpers.core import hookenv, host
from charmhelpers.payload.execd import execd_preinstall

from charmhelpers.core.hookenv import log, DEBUG, ERROR, WARNING
from charmhelpers.fetch import (
    apt_install, apt_update, add_source, filter_installed_packages
)
from utils import render_template

hooks = hookenv.Hooks()


def chownr(path, owner, group):
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(group).gr_gid
    for root, dirs, files in os.walk(path):
        for momo in dirs:
            os.chown(os.path.join(root, momo), uid, gid)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)


def install_upstart_scripts():
    for x in glob.glob('files/upstart/*.conf'):
        log('Installing upstart job:' + x, DEBUG)
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
        log("ERROR: {}".format(p.returncode), hookenv.ERROR)
        sys.exit(p.returncode)

    raise subprocess.CalledProcessError(
        p.returncode, command, '\n'.join(lines))


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


def emit_cc_conf():
    if 'config_ok' in local_state:
        del local_state['config_ok']
    local_state.save()
    cc_context = {}
    #cc_context['domain'] = config_data['domain']
    cc_context['cc_ip'] = hookenv.unit_private_ip()
    # do we need CC port?
    cc_context['cc_port'] = config_data['cc_port']
    cc_context['system_domain_organization'] = \
        config_data['system_domain_organization']
    params = (
        'nats_address', 'nats_port', 'nats_user', 'nats_password',
        'system_domain',
        'uaa_address',
        )
    for item in params:
        if item in local_state:
            cc_context[item] = local_state[item]
        else:
            log(('#emit_cc_conf: missing %s item.' % item), ERROR)
            return False
    local_state['config_ok'] = True
    local_state.save()
    os.chdir(hookenv.charm_dir())
    with open(CC_CONFIG_FILE, 'w') as cc_conf:
        cc_conf.write(render_template('cloud_controller_ng.yml', cc_context))
    return True


def emit_nginx_conf():
    nginx_context = {
        'nginx_port': config_data['nginx_port'],
    }
    os.chdir(hookenv.charm_dir())
    with open(NGINX_CONFIG_FILE, 'w') as nginx_conf:
        nginx_conf.write(render_template('nginx.conf', nginx_context))


def port_config_changed(port):
    '''Cheks if value of port changed close old port and open a new one'''
    if port in local_state:
        if local_state[port] != config_data[port]:
            log('Stored value for {} isn\'t equal to config data'.format(port),
                DEBUG)
            log('Closing port {}'.format(str(local_state[port])), WARNING)
            hookenv.close_port(local_state[port])
            local_state[port] = config_data[port]
            hookenv.open_port(config_data[port])
    else:
        local_state[port] = config_data[port]
    local_state.save()
    hookenv.open_port(config_data[port])


def cc_db_migrate():
    if not 'ccdbmigrated' in local_state:
        log("Starting db:migrate...", DEBUG)
        os.chdir(CC_DIR)
        #TODO: make it idempotent by deleting existing db if exists
        run(['sudo', '-u', 'vcap', '-g', 'vcap',
            'CLOUD_CONTROLLER_NG_CONFIG={}'.format(CC_CONFIG_FILE),
            'bundle', 'exec', 'rake', 'db:migrate'])
        local_state['ccdbmigrated'] = True
        local_state.save()


@hooks.hook()
def install():
    execd_preinstall()
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    apt_install(packages=filter_installed_packages(CC_PACKAGES), fatal=True)
    host.adduser('vcap')
    if not os.path.isfile(CC_DB_FILE):
        host.write_file(CC_DB_FILE, '', owner='vcap', group='vcap', perms=0775)
    dirs = [CC_RUN_DIR, NGINX_RUN_DIR, CC_LOG_DIR, NGINX_LOG_DIR,
            '/var/vcap/data/cloud_controller_ng/tmp/uploads',
            '/var/vcap/data/cloud_controller_ng/tmp/staged_droplet_uploads',
            '/var/vcap/nfs/store']
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    chownr('/var/vcap', owner='vcap', group='vcap')
    chownr(CF_DIR, owner='vcap', group='vcap')
    install_upstart_scripts()
    #reconfigure NGINX as upstart job and use specific config file
    run(['update-rc.d', '-f', 'nginx', 'remove'])
    host.service_stop('nginx')
    if os.path.isfile('/etc/init.d/nginx'):
        try:
            os.remove('/etc/init.d/nginx')
        except OSError:
            pass


@hooks.hook("config-changed")
def config_changed():
    local_state['config_ok'] = False
    local_state.save()
    port_config_changed('nginx_port')
    emit_nginx_conf()
    if host.service_running('cf-nginx'):
        #TODO replace with config reload
        host.service_restart('cf-nginx')
    if emit_cc_conf() and host.service_running('cf-cloudcontroller'):
        host.service_restart('cf-cloudcontroller')


@hooks.hook()
def start():
    if 'config_ok' in local_state:
        if not 'ccdbmigrated' in local_state:
            cc_db_migrate()
        else:
            if not host.service_running('cf-cloudcontroller'):
                log("Starting cloud controller as upstart job")
                host.service_start('cf-cloudcontroller')
            if (not host.service_running('cf-nginx')) and \
                    host.service_running('cf-cloudcontroller'):
                log("Starting NGINX")
                host.service_start('cf-nginx')
            hookenv.open_port(local_state['nginx_port'])


@hooks.hook()
def stop():
    if host.service_running('cf-nginx'):
        host.service_stop('cf-nginx')
    if host.service_running('cf-cloudcontroller'):
        host.service_stop('cf-cloudcontroller')
    hookenv.close_port(local_state['nginx_port'])


@hooks.hook('db-relation-changed')
def db_relation_changed():
    pass


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    for relid in hookenv.relation_ids('nats'):
        local_state['nats_address'] = hookenv.relation_get('nats_address')
        local_state['nats_port'] = hookenv.relation_get('nats_port')
        local_state['nats_user'] = hookenv.relation_get('nats_user')
        local_state['nats_password'] = \
            hookenv.relation_get('nats_password')
        local_state.save()
        config_changed()
        start()


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    stop()


@hooks.hook('nats-relation-departed')
def nats_relation_departed():
    pass


####################### UAA relation hooks #####################


@hooks.hook('uaa-relation-changed')
def uaa_relation_changed():
    for relid in hookenv.relation_ids('uaa'):
        local_state['uaa_address'] = hookenv.relation_get('uaa_address')
        local_state.save()
        config_changed()
        start()


@hooks.hook('uaa-relation-broken')
def uaa_relation_broken():
    stop()


@hooks.hook('uaa-relation-departed')
def uaa_relation_departed():
    pass


####################### router relation hooks #####################


@hooks.hook('router-relation-changed')
def router_relation_changed():
    for relid in hookenv.relation_ids('router'):
        local_state['system_domain'] = hookenv.relation_get('router_address')
        local_state.save()
        config_changed()
        start()


@hooks.hook('router-relation-broken')
def router_relation_broken():
    stop()


@hooks.hook('router-relation-departed')
def router_relation_departed():
    pass

################################# Global variables ############################
config_data = hookenv.config()
hook_name = os.path.basename(sys.argv[0])
local_state = State('local_state.pickle')
CC_PACKAGES = ['cfcloudcontroller', 'cfcloudcontrollerjob']

CF_DIR = '/var/lib/cloudfoundry'
CC_DIR = '{}/cfcloudcontroller'.format(CF_DIR)
CC_CONFIG_DIR = '{}/jobs/config'.format(CC_DIR)
CC_CONFIG_FILE = '{}/cloud_controller_ng.yml'.format(CC_CONFIG_DIR)
CC_DB_FILE = '{}/db/cc.db'.format(CC_DIR)
CC_JOB_FILE = '/etc/init/cf-cloudcontroller.conf'
CC_LOG_DIR = '/var/vcap/sys/log/cloud_controller_ng'
CC_RUN_DIR = '/var/vcap/sys/run/cloud_controller_ng'

NGINX_JOB_FILE = '/etc/init/cf-nginx.conf'
NGINX_CONFIG_FILE = '{}/nginx.conf'.format(CC_CONFIG_DIR)
NGINX_RUN_DIR = '/var/vcap/sys/run/nginx_ccng'
NGINX_LOG_DIR = '/var/vcap/sys/log/nginx_ccng'

FOG_CONNECTION = '/var/vcap/nfs/store'

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
