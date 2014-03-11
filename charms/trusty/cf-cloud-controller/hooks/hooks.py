#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import time
import subprocess
import glob
import shutil
import pwd
import grp

from charmhelpers.core import hookenv, host
from charmhelpers.payload.execd import execd_preinstall

from charmhelpers.core.hookenv import log
from charmhelpers.fetch import (
    apt_install, apt_update, add_source
)
from utils import render_template
hooks = hookenv.Hooks()
config_data = hookenv.config()

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
        print 'Installing upstart job:', x
        shutil.copy(x, '/etc/init/')


def run(command, exit_on_error=True, quiet=False):
    '''Run a command and return the output.'''
    if not quiet:
        log("Running {!r}".format(command), hookenv.DEBUG)
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


def emit_cc_conf():
    cc_context = {
        'cc_ip': hookenv.unit_private_ip(),
        'cc_port': config_data['cc_port'],
        'nats_ip': config_data['nats_address'],
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


@hooks.hook()
def start():
    #reconfigure NGINX as upstart job and use specific config file
    run(['/etc/init.d/nginx', 'stop'])
    while host.service_running('nginx'):
        log("nginx still running")
        time.sleep(60)
    os.remove('/etc/init.d/nginx')
    run(['update-rc.d', '-f', 'nginx', 'remove'])
    log("Starting db:migrate...")
    os.chdir(CC_DIR)
    run(['sudo', '-u', 'vcap', '-g', 'vcap',
        'CLOUD_CONTROLLER_NG_CONFIG={}'.format(CC_CONFIG_FILE),
        'bundle', 'exec', 'rake', 'db:migrate'])
    log("Starting cloud controller daemonized in the background")
    host.service_start('cf-cloudcontroller')
    log("Starting NGINX")
    host.service_start('cf-nginx')


@hooks.hook("config-changed")
def config_changed():
    emit_cc_conf()
    emit_nginx_conf()
    hookenv.open_port(config_data['nginx_port'])


@hooks.hook()
def stop():
    host.service_stop('cf-nginx')
    host.service_stop('cf-cloudcontroller')
    hookenv.close_port(config_data['nginx_port'])


@hooks.hook('db-relation-changed')
def db_relation_changed():
    pass


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    nats_address = hookenv.relation_get('nats_address')
    log(nats_address)


@hooks.hook('nats-relation-broken')
def nats_relation_broken():
    pass


@hooks.hook('nats-relation-departed')
def nats_relation_departed():
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
