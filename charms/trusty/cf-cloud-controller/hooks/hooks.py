#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import time
import subprocess
import glob
import shutil

from libcf import editfile
from cloudfoundry import \
    (
        CF_DIR, CC_DIR, CC_CONFIG_DIR,
        CC_CONFIG_FILE, CC_DB_FILE, CC_JOB_FILE, CC_LOG_DIR,
        CC_RUN_DIR, NGINX_JOB_FILE, NGINX_CONFIG_FILE,
        NGINX_RUN_DIR, NGINX_LOG_DIR, FOG_CONNECTION,
        NATS_JOB_FILE, NATS_RUN_DIR, NATS_LOG_DIR,
        NATS_CONFIG_FILE, CC_PACKAGES
    )
from cloudfoundry import chownr
from charmhelpers.core import hookenv, host
from charmhelpers.payload.execd import execd_preinstall

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG,
    )
from charmhelpers.core.hookenv import log
from charmhelpers.fetch import (
    apt_install,
    apt_update,
    filter_installed_packages,
    add_source
)
from utils import render_template
hooks = hookenv.Hooks()
config_data = hookenv.config()


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


hooks = hookenv.Hooks()


def emit_natsconf():
    natscontext = {
        'nats_ip': hookenv.unit_private_ip(),
        'nats_port': config_data['nats_port'],
    }
    with open(NATS_CONFIG_FILE, 'w') as natsconf:
        natsconf.write(render_template('nats.yml', natscontext))


def emit_cc_conf():
    cc_context = {
        'cc_ip': hookenv.unit_private_ip(),
        'cc_port': config_data['cc_port'],
        'nats_ip': hookenv.unit_private_ip(),
        'nats_port': config_data['nats_port'],
    }
    with open(CC_CONFIG_FILE, 'w') as cc_conf:
        cc_conf.write(render_template('cloud_controller_ng.yml', cc_context))


def emit_nginx_conf():
    nginx_context = {
        'nginx_port': config_data['nginx_port'],
    }
    with open(NGINX_CONFIG_FILE, 'w') as nginx_conf:
        nginx_conf.write(render_template('nginx.conf', nginx_context))


@hooks.hook()
def install():
    execd_preinstall()
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    apt_install(packages=CC_PACKAGES, fatal=True)
    host.adduser('vcap')
    emit_natsconf()
    host.write_file(CC_DB_FILE, '', owner='vcap', group='vcap', perms=0775)
    dirs = [NATS_RUN_DIR, NATS_LOG_DIR, CC_RUN_DIR, NGINX_RUN_DIR, CC_LOG_DIR, NGINX_LOG_DIR,
            '/var/vcap/data/cloud_controller_ng/tmp', '/var/vcap/data/cloud_controller_ng/tmp/uploads',
            '/var/vcap/data/cloud_controller_ng/tmp/staged_droplet_uploads',
            '/var/vcap/nfs/store']
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    chownr('/var/vcap', owner='vcap', group='vcap')
    chownr(CF_DIR, owner='vcap', group='vcap')
    install_upstart_scripts()

@hooks.hook()
def start():
    #reconfigure NGINX as upstart job and use specific config file
    run(['/etc/init.d/nginx', 'stop'])
    while host.service_running('nginx'):
        log("nginx still running")
        time.sleep(60)
    os.remove('/etc/init.d/nginx')
    run(['update-rc.d', '-f', 'nginx', 'remove'])
    log("Starting NATS daemonized in the background")
    host.service_start('cf-nats')
    log("Starting db:migrate...")
    os.chdir(CC_DIR)
    run(['sudo', '-u', 'vcap', '-g', 'vcap', 'CLOUD_CONTROLLER_NG_CONFIG={}'.format(CC_CONFIG_FILE), 'bundle', 'exec', 'rake', 'db:migrate'])
    log("Starting cloud controller daemonized in the background")
    host.service_start('cf-cloudcontroller')
    log("Starting NGINX")
    host.service_start('cf-nginx')


@hooks.hook("config-changed")
def config_changed():
    emit_cc_conf()
    emit_natsconf()
    emit_nginx_conf()
    hookenv.open_port(config_data['nats_port'])
    hookenv.open_port(config_data['nginx_port'])


@hooks.hook()
def stop():
    host.service_stop('cf-nginx')
    host.service_stop('cf-cloudcontroller')
    host.service_stop('cf-nats')
    hookenv.close_port(config_data['nats_port'])
    hookenv.close_port(config_data['nginx_port'])


@hooks.hook('db-relation-changed')
def db_relation_changed():
    #TODO use python here
    '''
    CHEMA_USER=`relation-get schema_user`
    DB_SCHEMA_PASSWORD=`relation-get schema_password`
    DB_USER=`relation-get user`
    DB_USER_PASSWORD=`relation-get password`
    DB_DB=`relation-get database`
    DB_HOST=`relation-get private-address`
    DB_HOST_PORT=`relation-get port`
    DB_HOST_STATE=`relation-get state`

    juju-log $DB_SCHEMA_USER, $DB_SCHEMA_PASSWORD, $DB_USER, $DB_USER_PASSWORD, $DB_DB, $DB_HOST, $DB_HOST_PORT, $DB_HOST_STATE

    os.environ['CONFIG_DIR=/var/lib/cloudfoundry/cfcloudcontroller/jobs/config
    os.environ['CLOUD_CONTROLLER_NG_CONFIG=$CONFIG_DIR/cloud_controller_ng.yml
    RUN_DIR=/var/vcap/sys/run/cloud_controller_ng
    LOG_DIR=/var/vcap/sys/log/cloud_controller_ng
    TMPDIR=/var/vcap/data/cloud_controller_ng/tmp
    PIDFILE=$RUN_DIR/cloud_controller_ng.pid
    NFS_SHARE=/var/vcap/nfs

    mkdir -p $RUN_DIR
    mkdir -p $LOG_DIR
    mkdir -p $TMPDIR

    mkdir -p /var/vcap/nfs/shared

    sed -i "s|ccadmin:password@127.0.0.1:5432/ccdb|$DB_SCHEMA_USER:$DB_SCHEMA_PASSWORD@$DB_HOST:$DB_HOST_PORT/$DB_DB|" $CLOUD_CONTROLLER_NG_CONFIG

    juju-log $JUJU_REMOTE_UNIT modified its settings
    juju-log Relation settings:
    relation-get
    juju-log Relation members:
    relation-list
    '''


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    pass


hook_name = os.path.basename(sys.argv[0])
juju_log_dir = "/var/log/juju"

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
