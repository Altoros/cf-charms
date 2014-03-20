#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
from helpers.config_helper import find_config_parameter, emit_config
from helpers.upstart_helper import install_upstart_scripts
from helpers.state import State
from helpers.common import chownr, run

from charmhelpers.core import hookenv, host
from charmhelpers.payload.execd import execd_preinstall

from charmhelpers.core.hookenv import log, DEBUG, WARNING
from charmhelpers.fetch import (
    apt_install, apt_update, add_source, filter_installed_packages
)


hooks = hookenv.Hooks()


def emit_cloud_controller_config():
    config_items = ['nats_address', 'nats_port', 'nats_user', 'nats_password',
                    'domain', 'default_organization', 'cc_ip']

    emit_config('cloud_controller', config_items, local_state,
                'cloud_controller_ng.yml', CC_CONFIG_FILE)


def emit_nginx_config():
    config_items = ['nginx_port']
    emit_config('nginx', config_items, local_state,
                'nginx.conf', NGINX_CONFIG_FILE)


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
                log('{} port is not closed.'.format(str(local_state[port])),
                    WARNING)

    hookenv.open_port(config_data[port])
    local_state[port] = config_data[port]
    local_state.save()


def cc_db_migrate():
    if not local_state['ccdbmigrated']:
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
    local_state['cloud_controller_ok'] = False
    local_state['ccdbmigrated'] = False

    config_items = ['nats_address', 'nats_port', 'nats_user', 'nats_password',
                    'domain', 'default_organization', 'nginx_port']

    for key in config_items:
        value = find_config_parameter(key, hookenv, config_data)
        log(("%s = %s" % (key, value)), DEBUG)
        local_state[key] = value

    local_state['cc_ip'] = hookenv.unit_private_ip()
    local_state.save()

    port_config_changed('nginx_port')

    emit_nginx_config()
    emit_cloud_controller_config()

    stop()
    start()


@hooks.hook()
def start():
    if local_state['cloud_controller_ok']:
        if not local_state['ccdbmigrated']:
            cc_db_migrate()

        if not host.service_running('cf-cloudcontroller'):
            log("Starting cloud controller as upstart job")
            host.service_start('cf-cloudcontroller')

        if not host.service_running('cf-nginx'):
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
    config_changed()


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    stop()


@hooks.hook('nats-relation-departed')
def nats_relation_departed():
    pass


####################### router relation hooks #####################


@hooks.hook('router-relation-changed')
def router_relation_changed():
    # for relid in hookenv.relation_ids('router'):
    #     local_state['system_domain'] = hookenv.relation_get('router_address')
    #     local_state.save()
    #     config_changed()
    #     start()
    pass


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
