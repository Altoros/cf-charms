import sys
import os
import inspect
# import hookenv module from parent directory
charm_helpers_path = cmd_folder = os.path.realpath(os.path.abspath( '../' +\
    os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if charm_helpers_path not in sys.path:
    sys.path.insert(0, charm_helpers_path)
print charm_helpers_path
from core import hookenv

CC_PORT = hookenv.config('cc-port')
CF_USER = 'vcap'
CF_DIR = '/var/lib/cloudfoundry'
CC_DIR = '{}/cfcloudcontroller'.format(CF_DIR)
cc_config_dir = '{}/jobs/config'.format(CC_DIR)
cc_config_file = '{}/cloud_controller_ng.yml'.format(cc_config_dir)
cc_db_file = '{}/db/cc.db'.format(CC_DIR)
cc_job_file = '/etc/init/cf-cloudcontroller.conf'
cc_log_dir = '/var/vcap/sys/log/cloud_controller_ng'
cc_run_dir = '/var/vcap/sys/run/cloud_controller_ng'

nginx_job_file = '/etc/init/cf-nginx.conf'
nginx_config_file = '{}/nginx.conf'.format(cc_config_dir)
nginx_run_dir = '/var/vcap/sys/run/nginx_ccng'
nginx_log_dir = '/var/vcap/sys/log/nginx_ccng'

fog_connection = '/var/vcap/nfs/store'

NATS_PORT = hookenv.config('nats-port')
NATS_IP = hookenv.unit_private_ip()
nats_job_file = '/etc/init/cf-nats.conf'
nats_run_dir = '/var/vcap/sys/run/nats'
nats_log_dir = '/var/vcap/sys/log/nats'
nats_config_file = '{}/nats.yml'.format(cc_config_dir)

