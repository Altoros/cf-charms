#!/usr/bin/env python

"""
Test the cf-cloud-controller charm.

Usage:
    juju bootstrap
    TEST_TIMEOUT=900 ./test.py -v
    juju destroy-environment
"""
from amulet import Deployment
from amulet import deployer
d = deployer.Deployment()
SERIES = 'trusty'
TEST_CHARM = 'local:cf-cloud-controller'
#juju deploy  --repository=../../. local:trusty/cf-cloud-controller cc
