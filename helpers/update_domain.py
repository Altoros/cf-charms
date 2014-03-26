#!/usr/bin/env python

import os
import sys
import yaml
import subprocess


def juju_set_domain(service_name, domen_value):
    command = "juju set %s domain=%s" % (service_name, domen_value)
    print command
    os.system(command)


def service_public_address(service):
    return service['units'].values()[0]['public-address']


def update_domain():
    # XXX: this doesn't work, you don't have juju status
    # running from hooks. Its possible to do this
    # with the API server, but we really want a  relation
    # to the router if services depend on its IP
    print 'Fetching juju status...'
    juju_status_yaml = subprocess.check_output(['juju', 'status'])
    juju_status = yaml.load(juju_status_yaml)
    services = juju_status['services']
    router_service_name = 'router'

    print 'Router service name is: %s' % router_service_name

    if not router_service_name in services:
        print 'Router not found'
        exit(1)

    if not sys.argv[1:]:
        router_domain = service_public_address(services[router_service_name])
    else:
        router_domain = sys.argv[1:][0]

    print 'Router domain is: %s' % router_domain

    for service_name in services.keys():
        juju_set_domain(service_name, router_domain)

if __name__ == '__main__':
    update_domain()
