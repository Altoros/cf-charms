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


azure_vm_list = yaml.load(subprocess.check_output(['azure', 'vm', 'list', '--json']))

ports = ['80', '8080', '4022', '9022']

for vm in azure_vm_list:
    name = vm['VMName']
    for p in ports:
      try:
          command = 'azure vm endpoint create %s %s' % (name, p)
          print command
          os.system(command)
      except:
          print "Port can't be created %s:%s" % (name, p)