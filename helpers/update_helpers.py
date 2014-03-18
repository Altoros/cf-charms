#!/usr/bin/python

import os
import glob
import shutil
import inspect
# script filename (usually with path)
current_file = inspect.getfile(inspect.currentframe())
current_folder = os.path.dirname(os.path.abspath(current_file))
os.chdir(current_folder)

charms_folders = glob.glob('../charms/trusty/*')
helper_utils = ['update_helpers.py', 'update_hosts.py']

for charm_folder in charms_folders:
    charm_helper_folder = os.path.join(charm_folder, 'hooks', 'helpers')
    if os.path.exists(charm_helper_folder):
        shutil.rmtree(charm_helper_folder)
    print "Copying helpers to %s." % charm_helper_folder
    shutil.copytree(current_folder, charm_helper_folder)
    for util_file in helper_utils:
        os.remove(os.path.join(charm_helper_folder, util_file))
