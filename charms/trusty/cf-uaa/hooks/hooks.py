#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import pwd
import grp
import sys
import subprocess
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
    execute("/etc/init.d/tomcat7 stop")
    log("Installing SQLite jdbc driver jar into Tomcat lib directory if it doesn't exists ...", DEBUG)
    os.chdir(TOMCAT_HOME)
    if (not os.path.isfile("lib/" + SQLITE_JDBC_LIBRARY)):
        os.chdir('lib')
        run(['wget', 'https://bitbucket.org/xerial/sqlite-jdbc/downloads/sqlite-jdbc-3.7.2.jar'])
    log("Cleaning up old config files", DEBUG)
    run(['rm', '-rf', '/var/lib/cloudfoundry/cfuaa/jobs/config/*'])


@hooks.hook()
def start():
    log("start hook for UAA is called")

@hooks.hook()
def stop():
    log("stop hook for UAA is called")

@hooks.hook('config-changed')
def config_changed():
    log("config_changed hook for UAA is called")


#################### Global variables ####################
PACKAGES = ['cfuaa', 'cfuaajob', 'cfregistrar']
CF_DIR = '/var/lib/cloudfoundry'
RUN_DIR = '/var/vcap/sys/run/uaa'
LOG_DIR = '/var/vcap/sys/log/uaa'
CONFIG_FILE = os.path.join(CF_DIR, 'jobs/uaa/config/uaa.yml')
TOMCAT_HOME = '/var/lib/cloudfoundry/cfuaa/tomcat'
SQLITE_JDBC_LIBRARY = 'sqlite-jdbc-3.7.2.jar'