from charmhelpers.core import hookenv
import os
import pwd
import grp

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

NATS_JOB_FILE = '/etc/init/cf-nats.conf'
NATS_RUN_DIR = '/var/vcap/sys/run/nats'
NATS_LOG_DIR = '/var/vcap/sys/log/nats'
NATS_CONFIG_FILE = '{}/nats.yml'.format(CC_CONFIG_DIR)


def chownr(path, owner, group):
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(group).gr_gid
    for root, dirs, files in os.walk(path):
        for momo in dirs:
            os.chown(os.path.join(root, momo), uid, gid)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)
