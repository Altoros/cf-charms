import glob
import shutil
from charmhelpers.core.hookenv import log, DEBUG, charm_dir


def install_upstart_scripts():
    for x in glob.glob(charm_dir() + '/files/upstart/*.conf'):
        log('Installing upstart job:' + x, DEBUG)
        shutil.copy(x, '/etc/init/')
