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
ROUTER_PORT = hookenv.config('router_port')
