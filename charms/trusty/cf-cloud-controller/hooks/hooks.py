#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import time
import subprocess

from libcf import editfile
from charmhelpers.cloudfoundry import \
    (
        CC_PORT, CF_USER, CF_DIR, CC_DIR, CC_CONFIG_DIR,
        CC_CONFIG_FILE, CC_DB_FILE, CC_JOB_FILE, CC_LOG_DIR,
        CC_RUN_DIR, NGINX_JOB_FILE, NGINX_CONFIG_FILE,
        NGINX_RUN_DIR, NGINX_LOG_DIR, FOG_CONNECTION, NATS_PORT,
        NATS_IP, NATS_JOB_FILE, NATS_RUN_DIR, NATS_LOG_DIR,
        NATS_CONFIG_FILE,
    )
from charmhelpers.cloudfoundry import fs
from charmhelpers.core import hookenv, host

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG,
    )
from charmhelpers.core.hookenv import log
hooks = hookenv.Hooks()


#def log(msg, lvl=INFO):
#    myname = hookenv.local_unit().replace('/', '-')
#    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
#    with open('{}/{}-debug.log'.format(juju_log_dir, myname), 'a') as f:
#        f.write('{} {}: {}\n'.format(ts, lvl, msg))
#    hookenv.log(msg, lvl)


def run(command, exit_on_error=True, quiet=False):
    '''Run a command and return the output.'''
    if not quiet:
        log("Running {!r}".format(command), DEBUG)
    p = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        shell=isinstance(command, basestring))
    p.stdin.close()
    lines = []
    for line in p.stdout:
        if line:
            if not quiet:
                print line
            lines.append(line)
        elif p.poll() is not None:
            break

    p.wait()

    if p.returncode == 0:
        return '\n'.join(lines)

    if p.returncode != 0 and exit_on_error:
        log("ERROR: {}".format(p.returncode), ERROR)
        sys.exit(p.returncode)

    raise subprocess.CalledProcessError(
        p.returncode, command, '\n'.join(lines))


hooks = hookenv.Hooks()


@hooks.hook()
def install():
    run(['apt-key', 'adv', '--keyserver', 'keyserver.ubuntu.com', '--recv-keys', '4C430C3C2828E07D'])
    run(['add-apt-repository', 'ppa:cf-charm/ppa'])
    run(['apt-get', 'update'])
    #run(['apt-get', 'install', 'curl', 'git', 'libgd3', 'libjbig0', 'libjpeg-turbo8', 'libjpeg8', 'libtiff5',\
            #'libvpx1', 'charm-helper-sh', 'nginx-extras', 'libgd-tools', 'nginx-doc', 'fcgiwrap', 'sqlite3', 'libsqlite3-dev'])
    run(['apt-get', 'install', '-y', 'cfcloudcontroller'])
    run(['apt-get', 'install', '-y', 'cfcloudcontrollerjob'])
    host.adduser(CF_USER)
    content = '''net: {nats_ip}
port: {nats_port}

pid_file: {npid}/nats.pid
log_file: {nlog}/nats.log

authorization:
  user: admin
  password: "password"
  timeout: 5
    '''.format(nats_port=NATS_PORT, nats_ip=NATS_IP, npid=NATS_RUN_DIR, nlog=NATS_LOG_DIR)
    host.write_file(NATS_CONFIG_FILE, content, owner=CF_USER, group=CF_USER)
    #todo use Session init instead of system
    content = '''description "Cloud Foundry NATS"
author "Alexander Prismakov<prismakov@gmail.com>"
start on starting cf-cloudcontroller or runlevel [2345]
stop on runlevel [!2345]
expect daemon
#apparmor load <profile-path>
setuid {user}
setgid {user}
respawn
normal exit 0
chdir {ccd}
exec bundle exec nats-server -c {natsyaml} -d
    '''.format(user=CF_USER, ccd=CC_DIR, natsyaml=NATS_CONFIG_FILE)
    host.write_file(NATS_JOB_FILE, content)
    content = '''description "Cloud Foundry cloud controller"
author "Alexander Prismakov<prismakov@gmail.com>"
start on runlevel [2345]
stop on runlevel [!2345]
#apparmor load <profile-path>
setuid {user}
setgid {user}
respawn
normal exit 0
chdir {ccd}
exec bundle exec bin/cloud_controller -m -c {ccyaml}
    '''.format(user=CF_USER, ccd=CC_DIR, ccyaml=CC_CONFIG_FILE)
    host.write_file(CC_JOB_FILE, content)
    content = '''description "Cloud Foundry NGINX"
author "Alexander Prismakov<prismakov@gmail.com>"
start on starting cf-cloudcontroller or runlevel [2345]
stop on runlevel [!2345]
#apparmor load <profile-path>
#setuid {user}
#setgid {user}
respawn
normal exit 0
exec /usr/sbin/nginx -c {nginxcf} -p /var/vcap
    '''.format(user=CF_USER, ccd=CC_DIR, nginxcf=NGINX_CONFIG_FILE)
    host.write_file(NGINX_JOB_FILE, content)
    host.write_file(CC_DB_FILE, '', owner=CF_USER, group=CF_USER, perms=0664)
    dirs = [NATS_RUN_DIR, NATS_LOG_DIR, CC_RUN_DIR, NGINX_RUN_DIR, CC_LOG_DIR, NGINX_LOG_DIR,
            '/var/vcap/data/cloud_controller_ng/tmp', '/var/vcap/data/cloud_controller_ng/tmp/uploads',
            '/var/vcap/data/cloud_controller_ng/tmp/staged_droplet_uploads',
            '/var/vcap/nfs/store']
    for item in dirs:
        host.mkdir(item, owner=CF_USER, group=CF_USER, perms=1777)
    fs.chownr('/var/vcap', owner=CF_USER, group=CF_USER)
    fs.chownr(CF_DIR, owner=CF_USER, group=CF_USER)


@hooks.hook()
def start():
    #reconfigure NGINX as upstart job and use specific config file
    run(['/etc/init.d/nginx', 'stop'])
    run(['update-rc.d', '-f', 'nginx', 'remove'])
    log("Starting NATS daemonized in the background")
    host.service_start('cf-nats')
    log("Starting db:migrate...")
    os.chdir(CC_DIR)
    log("Starting NGINX")
    host.service_start('cf-nginx')
    run(['sudo', '-u', CF_USER, '-g', CF_USER, 'CLOUD_CONTROLLER_NG_CONFIG={}'.format(CC_CONFIG_FILE), 'bundle', 'exec', 'rake', 'db:migrate'])
    log("Starting cloud controller daemonized in the background")
    host.service_start('cf-cloudcontroller')


@hooks.hook("config-changed")
def config_changed():
    editfile.replace(CC_CONFIG_FILE, [('192.168.1.72', hookenv.unit_private_ip()),
                                      (r'nats:nats@127.0.0.1', 'admin:password@{}'.format(NATS_IP)),
                                      (r'postgres://ccadmin:password@127.0.0.1:5432/ccdb', 'sqlite://{}'.format(CC_DB_FILE)),
                                      (r'/var/vcap/jobs/cloud_controller_ng/config/runtimes.yml', '/var/lib/cloudfoundry/cfcloudcontroller/jobs/config/runtimes.yml'),
                                      (r'/var/vcap/jobs/cloud_controller_ng/config/stacks.yml', '/var/lib/cloudfoundry/cfcloudcontroller/jobs/config/stacks.yml')])
    editfile.replace(NGINX_CONFIG_FILE, [('user', r'#user'),
                                         ('nats:nats@127.0.0.1', 'admin:password@{}'.format(NATS_IP))])
    editfile.insert_line(NGINX_CONFIG_FILE, '  variables_hash_max_size 1024;', 'server_tokens')
    hookenv.open_port(NATS_PORT)
    hookenv.open_port(CC_PORT)

@hooks.hook()
def stop():
    host.service_stop('cf-nginx')
    host.service_stop('cf-cloudcontroller')
    host.service_stop('cf-nats')
    hookenv.close_port(NATS_PORT)
    hookenv.close_port(CC_PORT)


@hooks.hook('db-relation-changed')
def db_relation_changed():
    #TODO use python here
    '''
    CHEMA_USER=`relation-get schema_user`
    DB_SCHEMA_PASSWORD=`relation-get schema_password`
    DB_USER=`relation-get user`
    DB_USER_PASSWORD=`relation-get password`
    DB_DB=`relation-get database`
    DB_HOST=`relation-get private-address`
    DB_HOST_PORT=`relation-get port`
    DB_HOST_STATE=`relation-get state`

    juju-log $DB_SCHEMA_USER, $DB_SCHEMA_PASSWORD, $DB_USER, $DB_USER_PASSWORD, $DB_DB, $DB_HOST, $DB_HOST_PORT, $DB_HOST_STATE

    os.environ['CONFIG_DIR=/var/lib/cloudfoundry/cfcloudcontroller/jobs/config
    os.environ['CLOUD_CONTROLLER_NG_CONFIG=$CONFIG_DIR/cloud_controller_ng.yml
    RUN_DIR=/var/vcap/sys/run/cloud_controller_ng
    LOG_DIR=/var/vcap/sys/log/cloud_controller_ng
    TMPDIR=/var/vcap/data/cloud_controller_ng/tmp
    PIDFILE=$RUN_DIR/cloud_controller_ng.pid
    NFS_SHARE=/var/vcap/nfs

    mkdir -p $RUN_DIR
    mkdir -p $LOG_DIR
    mkdir -p $TMPDIR

    mkdir -p /var/vcap/nfs/shared

    sed -i "s|ccadmin:password@127.0.0.1:5432/ccdb|$DB_SCHEMA_USER:$DB_SCHEMA_PASSWORD@$DB_HOST:$DB_HOST_PORT/$DB_DB|" $CLOUD_CONTROLLER_NG_CONFIG

    juju-log $JUJU_REMOTE_UNIT modified its settings
    juju-log Relation settings:
    relation-get
    juju-log Relation members:
    relation-list
    '''


@hooks.hook('nats-relation-changed')
def nats_relation_changed():
    pass


hook_name = os.path.basename(sys.argv[0])
juju_log_dir = "/var/log/juju"

if __name__ == '__main__':
    # Hook and context overview. The various replication and client
    # hooks interact in complex ways.
    log("Running {} hook".format(hook_name))
    if hookenv.relation_id():
        log("Relation {} with {}".format(
            hookenv.relation_id(), hookenv.remote_unit()))
    hooks.execute(sys.argv)
