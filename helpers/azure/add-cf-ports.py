#!/usr/bin/env python

#
# To install azure command line tools run following commands: 
#     sudo apt-get install npm nodejs
#     sudo npm install azure
# Then authenticate :
#     azure account download # this will open browser and download cert file
#     azure import <cert-file-path>
# 

import os
import yaml
import subprocess

'azure vm list --json'


azure_vm_list = yaml.load(subprocess.check_output(['juju', 'status']))

ports = [80, 8080, 4022, 9022]

ports_description = ''

for vm in azure_vm_list:
    name = vm['VMName']
    'azure vm endpoint create-multiple --enable-direct-server-return %s' % ports_description
