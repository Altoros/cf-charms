import sys
import os
import inspect
# import hookenv module from parent directory
charm_helpers_path = cmd_folder = os.path.realpath(os.path.abspath('../' + os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if charm_helpers_path not in sys.path:
    sys.path.insert(0, charm_helpers_path)
print charm_helpers_path
from core import hookenv

CC_PORT = hookenv.config('cc-port')
CF_USER = 'vcap'
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

NATS_PORT = hookenv.config('nats-port')
NATS_IP = hookenv.unit_private_ip()
NATS_JOB_FILE = '/etc/init/cf-nats.conf'
NATS_RUN_DIR = '/var/vcap/sys/run/nats'
NATS_LOG_DIR = '/var/vcap/sys/log/nats'
NATS_CONFIG_FILE = '{}/nats.yml'.format(CC_CONFIG_DIR)
