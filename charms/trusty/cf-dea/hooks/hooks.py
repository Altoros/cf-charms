#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import glob
import shutil
from charmhelpers.core import hookenv, host
from charmhelpers.core.hookenv import log, charm_dir

from charmhelpers.fetch import (
    apt_install, apt_update, add_source, filter_installed_packages
)
# from utils import render_template

from helpers.config_helper import emit_config
from helpers.upstart_helper import install_upstart_scripts
from helpers.common import chownr
from helpers.state import State

hooks = hookenv.Hooks()


def emit_warden_config():
    required_config_items = []

    emit_config('warden', required_config_items, local_state,
                'warden.yml', WARDEN_CONFIG_PATH)


def emit_dea_config():
    required_config_items = ['nats_user', 'nats_password', 'nats_address',
                             'nats_port', 'domain']

    emit_config('dea', required_config_items, local_state,
                'dea.yml', DEA_CONFIG_PATH)


@hooks.hook()
def install():
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    apt_install(packages=filter_installed_packages(DEA_PACKAGES), fatal=True)
    install_upstart_scripts()
    emit_warden_config()
    host.adduser('vcap')
    host.mkdir(CF_DIR, owner='vcap', group='vcap', perms=0775)
    #os.chdir(CF_DIR)
    #run(['gem', 'install', 'bundle', 'eventmachine'])
    #run(['gem', 'install', 'bundle'])
    #run(['git', 'clone', 'https://github.com/cloudfoundry/dea_ng.git'])
    dirs = [DEA_PIDS_DIR, DEA_CACHE_DIR, DEA_BP_CACHE_DIR]
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    os.chdir(DEA_DIR)
    #run(['git', 'submodule', 'update', '--init'])
    #run(['bundle', 'install', '--without', 'test'])
    chownr(CF_DIR, 'vcap', 'vcap')
    for x in glob.glob(charm_dir() + '/files/bin/*'):
        shutil.copy(x, os.path.join(DEA_DIR, 'jobs', 'bin'))

    # install warden
    os.chdir(WARDEN_DIR)
    os.system('sudo bundle install --standalone '
              '--deployment --without=development test')
    os.system('sudo bundle exec rake setup[config/linux.yml]')
    os.system('sudo bundle exec rake warden:start[config/linux.yml]')
    os.system('sudo bundle exec rake setup:bin')


# /var/lib/cloudfoundry/cfdea/jobs

@hooks.hook()
def start():
    if not host.service_running('cf-dea'):
        log("Starting DEA as upstart job")
        host.service_start('cf-dea')
    if not host.service_running('cf-warden'):
        log("Starting Warden as upstart job")
        host.service_start('cf-warden')


@hooks.hook("config-changed")
def config_changed():
    #port_config_changed('router_port')
    local_state['domain'] = config_data['domain']
    local_state.save()
    emit_dea_config()
    emit_warden_config()
    if local_state['dea_ok'] and host.service_running('cf-dea'):
        #TODO replace with config reload
        log("Restarting DEA")
        host.service_restart('cf-dea')


@hooks.hook()
def stop():
    if host.service_running('cf-dea'):
        host.service_stop('cf-dea')
    if host.service_running('cf-warden'):
        host.service_stop('cf-warden')
#        hookenv.close_port(local_state['router_port'])


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    #TODO add checks of values
    nats_values = ('nats_address', 'nats_port',
                   'nats_user', 'nats_password')
    for value in nats_values:
        local_state[value] = hookenv.relation_get(value)
    local_state.save()
    config_changed()
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
                'debootstrap', 'quota', 'libxml2-dev', 'cfwarden',
                'cfdea', 'cfdeajob', 'cfrootfs', 'cfbuildpackcache']

CF_DIR = '/var/lib/cloudfoundry'
DEA_DIR = os.path.join(CF_DIR, 'cfdea')
WARDEN_DIR = os.path.join(CF_DIR, 'cfwarden', 'warden')
DEA_PIDS_DIR = os.path.join(DEA_DIR, 'pids')
DEA_CACHE_DIR = os.path.join(DEA_DIR, 'cache')
DEA_BP_CACHE_DIR = os.path.join(DEA_DIR, 'buildpack_cache')
DEA_CONFIG_PATH = os.path.join(DEA_DIR, 'config', 'dea.yml')
WARDEN_CONFIG_PATH = os.path.join(WARDEN_DIR, 'config', 'warden.yml')
local_state = State('local_state.pickle')

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
