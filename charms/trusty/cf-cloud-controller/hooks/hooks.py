#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import time
import subprocess

from charmhelpers.cloudfoundry import fs
from charmhelpers.core import hookenv, host

from charmhelpers.core.hookenv import \
    (
        CRITICAL, ERROR, WARNING, INFO, DEBUG,
    )

cf_user = 'vcap'
cf_dir = '/var/lib/cloudfoundry'
cc_dir = '{}/cfcloudcontroller'.format(cf_dir)
cc_config_dir = '{}/jobs/config'.format(cc_dir)
cc_config_file = '{}/cloud_controller_ng.yml'.format(cc_config_dir)
nats_config_file = '{}/nats.yml'.format(cc_config_dir)
nginx_config_file = '{}/nginx.conf'.format(cc_config_dir)
nats_run_dir = '/var/vcap/sys/run/nats'
nats_log_dir = '/var/vcap/sys/log/nats'
cc_db_file = '{}/db/cc.db'.format(cc_dir)
cc_job_file = '/etc/init/cf-cloudcontroller.conf'
nats_job_file = '/etc/init/cf-nats.conf'
nginx_job_file = '/etc/init/cf-nginx.conf'
cc_log_dir = '/var/vcap/sys/log/cloud_controller_ng'
cc_run_dir = '/var/vcap/sys/run/cloud_controller_ng'
nginx_run_dir = '/var/vcap/sys/run/nginx_ccng'
nginx_log_dir = '/var/vcap/sys/log/nginx_ccng'
fog_connection = '/var/vcap/nfs/store'
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
    '''.format(user=cf_user, ccd=cc_dir, natsyaml=nats_config_file)
    host.write_file(nats_job_file, content)
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
    '''.format(user=cf_user, ccd=cc_dir, ccyaml=cc_config_file)
    host.write_file(cc_job_file, content)
#    content = '''description "Cloud Foundry NGINX"
#author "Alexander Prismakov<prismakov@gmail.com>"
#start on runlevel [2345]
#stop on runlevel [!2345]
##apparmor load <profile-path>
#setuid {user}
#setgid {user}
#respawn
#normal exit 0
#exec /usr/sbin/nginx -c {nginxcf} -p /var/vcap
#    '''.format(user=cf_user, ccd=cc_dir, nginxcf=nginx_config_file)
#    host.write_file(nginx_job_file, content)
    host.write_file(cc_db_file, '', owner=cf_user, group=cf_user, perms=0664)
    dirs = [nats_run_dir, nats_log_dir, cc_run_dir, nginx_run_dir, cc_log_dir, nginx_log_dir,
            '/var/vcap/data/cloud_controller_ng/tmp', '/var/vcap/data/cloud_controller_ng/tmp/uploads',
            '/var/vcap/data/cloud_controller_ng/tmp/staged_droplet_uploads',
            '/var/vcap/nfs/store']
    for item in dirs:
        host.mkdir(item, owner=cf_user, group=cf_user, perms=1777)
    fs.chownr('/var/vcap', owner=cf_user, group=cf_user)
    fs.chownr(cf_dir, owner=cf_user, group=cf_user)


@hooks.hook()
def start():
    log("Starting NATS daemonized in the background")
    host.service_start('cf-nats')
    log("Starting db:migrate...")
    os.chdir(cc_dir)
    run(['sudo', '-u', cf_user, '-g', cf_user, 'CLOUD_CONTROLLER_NG_CONFIG={}'.format(cc_config_file), 'bundle', 'exec', 'rake', 'db:migrate'])
    log("Starting cloud controller daemonized in the background")
    host.service_start('cf-cloudcontroller')
 #   log("Starting NGINX")
 #   host.service_start('cf-nginx')


@hooks.hook("config-changed")
def config_changed():
    tmp_file_name = '{}.next'.format(cc_config_file)
    #todo optimize code below
    with open(tmp_file_name, "wt") as fout:
        with open(cc_config_file, "rt") as fin:
            for line in fin:
                new_line = line.replace('192.168.1.72', hookenv.unit_private_ip())
                fout.write(new_line)
    os.rename(tmp_file_name, cc_config_file)
    with open(tmp_file_name, "wt") as fout:
        with open(cc_config_file, "rt") as fin:
            for line in fin:
                new_line = line.replace(r'nats:nats@127.0.0.1', 'admin:password@{}'.format(hookenv.unit_private_ip()))
                fout.write(new_line)
    os.rename(tmp_file_name, cc_config_file)
    with open(tmp_file_name, "wt") as fout:
        with open(cc_config_file, "rt") as fin:
            for line in fin:
                new_line = line.replace(r'postgres://ccadmin:password@127.0.0.1:5432/ccdb', 'sqlite://{}'.format(cc_db_file))
                fout.write(new_line)
    os.rename(tmp_file_name, cc_config_file)
    with open(tmp_file_name, "wt") as fout:
        with open(cc_config_file, "rt") as fin:
            for line in fin:
                new_line = line.replace(r'/var/vcap/jobs/cloud_controller_ng/config/runtimes.yml', '/var/lib/cloudfoundry/cfcloudcontroller/jobs/config/runtimes.yml')
                fout.write(new_line)
    os.rename(tmp_file_name, cc_config_file)
    with open(tmp_file_name, "wt") as fout:
        with open(cc_config_file, "rt") as fin:
            for line in fin:
                new_line = line.replace(r'/var/vcap/jobs/cloud_controller_ng/config/stacks.yml', '/var/lib/cloudfoundry/cfcloudcontroller/jobs/config/stacks.yml')
                fout.write(new_line)
    os.rename(tmp_file_name, cc_config_file)
    tmp_file_name = '{}.next'.format(nginx_config_file)
    with open(tmp_file_name, "wt") as fout:
        with open(nginx_config_file, "rt") as fin:
            for line in fin:
                new_line = line.replace('user', r'#user')
                new_line = line.replace('nats:nats@127.0.0.1', 'admin:password@{}'.format(hookenv.unit_private_ip()))
                fout.write(new_line)
    os.rename(tmp_file_name, nginx_config_file)
    #TODO use pure python here
    run(['sed', '-i', r'/server_tokens/ a\  variables_hash_max_size 1024;', nginx_config_file])


@hooks.hook()
def stop():
    #    host.service_stop('cf-nginx')
    host.service_stop('cf-cloudcontroller')
    host.service_stop('cf-nats')


@hooks.hook('db-relation-changed')
def db_relation_changed():
    #TODO use python
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
