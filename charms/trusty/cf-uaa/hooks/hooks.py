#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import pwd
import grp
import sys
import subprocess
# from subprocess import call
import glob
#import shutil
import cPickle as pickle

from charmhelpers.core import hookenv, host
from charmhelpers.core.hookenv import log, DEBUG, ERROR
#from charmhelpers.payload.execd import execd_preinstall

from charmhelpers.fetch import (
    apt_install, apt_update, add_source, filter_installed_packages
)
from lib import utils

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG,
    )

from charmhelpers.fetch import (
    apt_install,
    apt_update,
    filter_installed_packages,
    add_source
)

from utils import render_template


config_data = hookenv.config()
hooks = hookenv.Hooks()


@hooks.hook()
def install():
    add_source(config_data['source'], config_data['key'])
    apt_update(fatal=True)
    log("Installing required packages", DEBUG)
    apt_install(packages=filter_installed_packages(PACKAGES), fatal=True)
    log("Creating 'vcap' user which will run everything related to CF", DEBUG)
    host.adduser('vcap')
    log("Creating necessary directories for pids and logs", DEBUG)
    dirs = [RUN_DIR, LOG_DIR]
    for item in dirs:
        host.mkdir(item, owner='vcap', group='vcap', perms=0775)
    utils.chownr('/var/vcap', owner='vcap', group='vcap')
    utils.chownr(CF_DIR, owner='vcap', group='vcap')
    log("Stopping Tomcat ...", DEBUG)
    os.system("/etc/init.d/tomcat7 stop")
    log("Installing SQLite jdbc driver jar into Tomcat lib directory if it doesn't exists ...", DEBUG)
    os.chdir(TOMCAT_HOME)
    if (not os.path.isfile("lib/" + SQLITE_JDBC_LIBRARY)):
        os.chdir('lib')
        subprocess.call(['wget', 'https://bitbucket.org/xerial/sqlite-jdbc/downloads/sqlite-jdbc-3.7.2.jar'])
    log("Cleaning up old config files", DEBUG)
    subprocess.call(['rm', '-rf', os.path.join(CONFIG_DIR, '*')])


    with open(UAA_CONFIG_FILE, 'w') as uaa_config_file:
        uaa_config_file.write(render_template('uaa.yml', {}))

    with open(VARZ_CONFIG_FILE, 'w') as varz_config_file:
        varz_config_file.write(render_template('varz.yml', {varz_user: 'user', varz_password: 'password'}))

    tompcat_varz_folder = os.path.join(TOMCAT_HOME, 'webapps', 'varz', 'WEB-INF')
    subprocess.call('mkdir -p {}'.format(tompcat_varz_folder))
    os.mv(VARZ_CONFIG_FILE, tompcat_varz_folder)
    os.system('export UAA_CONFIG_PATH={}'.format(CONFIG_DIR))

@hooks.hook()
def start():
    log("start hook for UAA is called")
    os.chdir(TOMCAT_HOME)
    subprocess.call(['sudo', '-u', 'vcap', '-g', 'vcap',
                     'UAA_CONFIG_PATH={}'.format(CONFIG_DIR), './bin/startup.sh'])


@hooks.hook()
def stop():
    log("stop hook for UAA is called")
    os.chdir(TOMCAT_HOME)
    subprocess.call(['sudo', '-u', 'vcap', '-g', 'vcap', './bin/shutdown.sh'])


@hooks.hook('config-changed')
def config_changed():
    log("config_changed hook for UAA is called")


#################### Global variables ####################
config_data = hookenv.config()
hook_name = os.path.basename(sys.argv[0])

CF_DIR = '/var/lib/cloudfoundry'

PACKAGES = ['cfuaa', 'cfuaajob', 'cfregistrar']
RUN_DIR = '/var/vcap/sys/run/uaa'
LOG_DIR = '/var/vcap/sys/log/uaa'
CONFIG_DIR = os.path.join(CF_DIR, 'jobs/uaa/config')
UAA_CONFIG_FILE = os.path.join(CONFIG_DIR, 'uaa.yml')
VARZ_CONFIG_FILE = os.path.join(CONFIG_DIR, 'varz.yml')
TOMCAT_HOME = '/var/lib/cloudfoundry/cfuaa/tomcat'
SQLITE_JDBC_LIBRARY = 'sqlite-jdbc-3.7.2.jar'


if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
