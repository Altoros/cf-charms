#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import time
import subprocess

from charmhelpers.cloudfoundry import \
    (
        cf_dir, cf_user, nats_run_dir, nats_log_dir, nats_config_file, cc_dir,
        nats_job_file, cc_db_file,
    )
from charmhelpers.cloudfoundry import fs
from charmhelpers.core import hookenv, host

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG,
    )

hooks = hookenv.Hooks()


def log(msg, lvl=INFO):
    '''Log a message.

    Per Bug #1208787, log messages sent via juju-log are being lost.
    Spit messages out to a log file to work around the problem.
    It is also rather nice to have the log messages we explicitly emit
    in a separate log file, rather than just mashed up with all the
    juju noise.
    '''
    myname = hookenv.local_unit().replace('/', '-')
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    with open('{}/{}-debug.log'.format(juju_log_dir, myname), 'a') as f:
        f.write('{} {}: {}\n'.format(ts, lvl, msg))
    hookenv.log(msg, lvl)


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
            # LP:1274460 & LP:1259490 mean juju-log is no where near as
            # useful as we would like, so just shove a copy of the
            # output to stdout for logging.
            # log("> {}".format(line), DEBUG)
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
    host.adduser(cf_user)
    content = '''net: {}
port: 4222

pid_file: {}/nats.pid
log_file: {}/nats.log

authorization:
  user: admin
  password: "password"
  timeout: 5
    '''.format(hookenv.unit_private_ip(), nats_run_dir, nats_log_dir)
    host.write_file(nats_config_file, content, owner=cf_user, group=cf_user)
    content = '''description "Cloud Foundry NATS"
author "Alexander Prismakov<prismakov@gmail.com>"
start on runlevel [2345]
stop on runlevel [!2345]
expect daemon
#apparmor load <profile-path>
setuid {user}
setgid {user}
respawn
normal exit 0
chdir {ccd}
exec bundle exec nats-server -c {natsyaml} -d
    '''.format(user=cf_user, ccd=cc_dir, natsyaml=nats_config_file)
    host.write_file(nats_job_file, content)
    fs.chownr(cf_dir, owner=cf_user, group=cf_user)
    host.write_file(cc_db_file, content, owner=cf_user, group=cf_user, perms=0664)
    host.mkdir(nats_run_dir, owner=cf_user, group=cf_user, perms=1777)
    host.mkdir(nats_log_dir, owner=cf_user, group=cf_user, perms=1777)


@hooks.hook()
def start():
    log("Starting NATS daemonized in the background")
    host.service_start('cf-nats')
    log("Starting db:migrate...")
    os.chdir(cc_dir)
    #run(['bundle', 'exec', 'rake', 'db:migrate'])
    #log("Starting CF cloud controller...")
    '''
    bundle exec bin/cloud_controller -m -c $CLOUD_CONTROLLER_NG_CONFIG &
    juju-log "Starting nginx..."
    /usr/sbin/nginx -c $NGINX_CONF -p /var/vcap
    '''


@hooks.hook("config-changed")
def config_changed():
    '''
    os.environ['DB_PATH=/var/lib/cloudfoundry/cfcloudcontroller/db/cc.db

    sed -i "s|192.168.1.72|`unit-get private-address`|" $CLOUD_CONTROLLER_NG_CONFIG
    sed -i "s|nats:nats@127.0.0.1|admin:password@`unit-get private-address`|" $CLOUD_CONTROLLER_NG_CONFIG
    sed -i "s|postgres://ccadmin:password@127.0.0.1:5432/ccdb|sqlite://$DB_PATH|" $CLOUD_CONTROLLER_NG_CONFIG
    sed -i "s|/var/vcap/jobs/cloud_controller_ng/config/runtimes.yml|/var/lib/cloudfoundry/cfcloudcontroller/jobs/config/runtimes.yml|" $CLOUD_CONTROLLER_NG_CONFIG
    sed -i "s|/var/vcap/jobs/cloud_controller_ng/config/stacks.yml|/var/lib/cloudfoundry/cfcloudcontroller/jobs/config/stacks.yml|" $CLOUD_CONTROLLER_NG_CONFIG

    sed -i "s|user|#user|" $NGINX_CONF
    sed -i "/server_tokens/ a\  variables_hash_max_size 1024;" $NGINX_CONF
    '''


@hooks.hook()
def stop():
    host.service_stop('cf-nats')


@hooks.hook('db-relation-changed')
def db_relation_changed():
    #TODO
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
