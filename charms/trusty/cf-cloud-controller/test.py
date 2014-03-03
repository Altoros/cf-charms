#!/usr/bin/python3

"""
Test the cf-cloud-controller charm.

Usage:
    juju bootstrap
    TEST_TIMEOUT=900 ./test.py -v
    juju destroy-environment
"""

from amulet import Deployment
from amulet import deployer
import subprocess
#SERIES = 'trusty'
TEST_CHARM = 'local:trusty/cf-cloud-conroller'
#subprocess.check_output(['juju', 'deploy', '--repository=../../.', 'local:trusty/cf-cloud-controller', 'cc'])
d = deployer.Deployment()
d.add('cc', charm=TEST_CHARM)
#d.setup()
