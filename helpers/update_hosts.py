#!/usr/bin/env python

import os
import yaml
import subprocess
import socket

# try to use import shlex

def run_via_ssh(ssh_prefix, command):
    if command.find('"') > 0:
        print ("WARNING: command %s hould not contain " 
               "double quotes.") % command
    command = '%s "%s" > /dev/null 2>&1' % (ssh_prefix, command)
    #print command
    subprocess.call(command, shell=True)

def first_unit_of(service):
    try:
        return service['units'].values()[0]
    except:
        print "Can't find units in %s" % service

def service_host(service):
    try:
        return first_unit_of(service)['public-address']
    except:
        print "Can't find public-address in %s" % service

def service_ip_address(service):
    return socket.gethostbyname(service_host(service))


def generate_add_host_command(host):
    return "sudo echo \'%s\' >> /etc/hosts" % host


def has_errors(service):
    return first_unit_of(service)['agent-state'] == 'error'

juju_status_yaml = subprocess.check_output(['juju', 'status'])
juju_status = yaml.load(juju_status_yaml)

router_service_name = 'router'
ssh_key_location = '~/.juju/ssh/juju_id_rsa'
services = juju_status['services']
if not router_service_name in services:
    print 'Router not found'
    exit(1)

router_public_ip = service_ip_address(services[router_service_name])

domain = 'example.net'
host_item = "%s api.%s uaa.%s" % (router_public_ip, domain, domain)

hosts_config = ["127.0.0.1 localhost",
                "::1 ip6-localhost ip6-loopback",
                "fe00::0 ip6-localnet",
                "ff00::0 ip6-mcastprefix",
                "ff02::1 ip6-allnodes",
                "ff02::2 ip6-allrouters",
                "ff02::3 ip6-allhosts",
                host_item]

for service in services.values():
    
    if has_errors(service):
        print 'Service {} has errors.'.format(service)
        continue

    service_ip = service_ip_address(service)
    print 'Processing machine {}'.format(service_ip)

    allow_access_to_hosts = ("sudo chown ubuntu /etc/hosts && " 
                             "sudo chmod +w /etc/hosts && "
                             "sudo echo '' > /etc/hosts")
    
    add_hosts = ' && '.join(map(generate_add_host_command, hosts_config))

    close_access_to_hosts = ("sudo chmod 644 /etc/hosts && " 
                             "sudo chown root /etc/hosts")

    super_command = ' && '.join([allow_access_to_hosts, add_hosts, close_access_to_hosts])

    ssh_prefix = "ssh -t -i %s ubuntu@%s" % (ssh_key_location, service_ip)
    run_via_ssh(ssh_prefix, super_command)


