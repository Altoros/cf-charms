#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import sys
import os
import subprocess

from charmhelpers.core import hookenv, host
from charmhelpers.core.hookenv import log
from charmhelpers.fetch import apt_install, apt_update, add_source

from utils import get_nats_config


hooks = hookenv.Hooks()

CHARM_DIR = os.environ['CHARM_DIR']


def install_files():
    subprocess.check_call(
        ["/usr/bin/install", "-o", "vcap", "-g", "vcap", "-m", "0400",
         os.path.join(CHARM_DIR, "files", "upstart", "cf-nats.conf"),
         "/etc/init/nats.conf"])

    # The package bin is borken (doesn't accept cli params)
    subprocess.check_call(
        ["/usr/bin/install", "-o", "vcap", "-g", "vcap", "-m", "0555",
         os.path.join(CHARM_DIR, "files", "nats-server"),
         "/usr/bin/nats-server"])


@hooks.hook()
def install():
    conf = hookenv.config()
    add_source(conf['source'])
    apt_update(fatal=True)
    apt_install(packages=NATS_PACKAGES, fatal=True)
    host.adduser('vcap')
    install_files()


@hooks.hook()
def start():
    log("Starting NATS as upstart job")
    if not host.service_running('nats'):
        host.service_start('nats')


@hooks.hook("config-changed")
def config_changed():
    # There are no real config options
    get_nats_config()
    if host.service_running('nats'):
        host.service_restart('nats')


@hooks.hook()
def stop():
    if host.service_running('nats'):
        host.service_stop('nats')


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    nats_conf = get_nats_config()
    address = hookenv.relation_get(
        'private-address', os.environ['JUJU_UNIT_NAME'])
    hookenv.relation_set(
        nats_address=address,
        nats_port=nats_conf['port'],
        nats_user=nats_conf['authorization']['user'],
        nats_password=nats_conf['authorization']['password'])

#################### Global variables ####################
NATS_PACKAGES = ['cfnats']


# Hook and context overview. The various replication and client
# hooks interact in complex ways.
if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except hookenv.UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
