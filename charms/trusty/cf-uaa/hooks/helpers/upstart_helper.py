import glob
import shutil
from charmhelpers.core.hookenv import log, DEBUG


def install_upstart_scripts():
    for x in glob.glob('files/upstart/*.conf'):
        log('Installing upstart job:' + x, DEBUG)
        shutil.copy(x, '/etc/init/')
