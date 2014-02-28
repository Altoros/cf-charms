#!/usr/bin/env python

"""
Test the cf-cloud-controller charm.

Usage:
    juju bootstrap
    TEST_TIMEOUT=900 ./test.py -v
    juju destroy-environment
"""
SERIES = 'trusty'
TEST_CHARM = 'local:cf-cloud-controller'

