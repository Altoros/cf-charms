#!/usr/bin/env python
# vim: et ai ts=4 sw=4:

import os
import sys
import time
from subprocess import call
from contextlib import contextmanager
from charmhelpers.core.host import *
from charmhelpers.core import hookenv, host

from charmhelpers.core.hookenv import (
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
    #TODO install needed packages in cc package
    log('Begin package installation')
    print 'Hi'
    run(['apt-key', 'adv', '--keyserver', 'keyserver.ubuntu.com', '--recv-keys', '4C430C3C2828E07D'])
    run(['add-apt-repository', 'ppa:cf-charm/ppa'])
    run(['apt-get', 'update'])
    #run(['apt-get', 'install', 'curl', 'git', 'libgd3', 'libjbig0', 'libjpeg-turbo8', 'libjpeg8', 'libtiff5',\
    #                    'libvpx1', 'charm-helper-sh', 'nginx-extras', 'libgd-tools', 'nginx-doc', 'fcgiwrap', 'sqlite3', 'libsqlite3-dev'])
    run(['apt-get', 'install', '-y', 'cfcloudcontroller', 'cfcloudcontrollerjob'])
    adduser('vcap')

@hooks.hook()
def start():
    config_dir = '/var/lib/cloudfoundry/cfcloudcontroller/jobs/config'
    os.environ['CONFIG_DIR'] = config_dir
    os.environ['CLOUD_CONTROLLER_NG_CONFIG'] = '{}/cloud_controller_ng.yml'.format(config_dir)
    cc_dir = '/var/lib/cloudfoundry/cfcloudcontroller'
    os.environ['CC_DIR'] = cc_dir
    nats_config = '{}/nats.yml'.format(config_dir)
    os.environ['NATS_CONFIG'] = nats_config
    os.environ['NGINX_CONF'] = '{}/nginx.conf'.format(config_dir)
    log("Starting NATS server...")
    os.chdir(cc_dir)
    run(['bundle', 'exec', 'nats-server', '-c', nats_config, '-d'])
    log("Starting db:migrate...")
    run(['bundle', 'exec', 'rake', 'db:migrate'])
    log("Starting CF cloud controller...")
    '''
    bundle exec bin/cloud_controller -m -c $CLOUD_CONTROLLER_NG_CONFIG &
    juju-log "Starting nginx..."
    /usr/sbin/nginx -c $NGINX_CONF -p /var/vcap
    '''

@hooks.hook("config-changed")
def config_changed():
   '''
    os.environ['CONFIG_DIR=/var/lib/cloudfoundry/cfcloudcontroller/jobs/config
    os.environ['CLOUD_CONTROLLER_NG_CONFIG=$CONFIG_DIR/cloud_controller_ng.yml
    os.environ['CC_DIR=/var/lib/cloudfoundry/cfcloudcontroller

    NATS_RUN_DIR=/var/vcap/sys/run/nats
    NATS_LOG_DIR=/var/vcap/sys/log/nats

    os.environ['NATS_CONFIG=$CONFIG_DIR/nats.yml
    os.environ['NGINX_CONF=$CONFIG_DIR/nginx.conf

    cat <<EOF > $NATS_CONFIG
    ---
    net: `unit-get private-address`
    port: 4222

    pid_file: $NATS_RUN_DIR/nats.pid
    log_file: $NATS_LOG_DIR/nats.log

    authorization:
      user: admin
      password: "password"
      timeout: 5
    EOF

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
    '''
    wait_pidfile() {
      pidfile=$1
      try_kill=$2
      timeout=${3:-0}
      force=${4:-0}
      countdown=$(( $timeout * 10 ))

      if [ -f "$pidfile" ]; then
        pid=$(head -1 "$pidfile")

        if [ -z "$pid" ]; then
          echo "Unable to get pid from $pidfile"
          exit 1
        fi

        if [ -e /proc/$pid ]; then
          if [ "$try_kill" = "1" ]; then
            echo "Killing $pidfile: $pid "
            kill $pid
          fi
          while [ -e /proc/$pid ]; do
            sleep 0.1
            [ "$countdown" != '0' -a $(( $countdown % 10 )) = '0' ] && echo -n .
            if [ $timeout -gt 0 ]; then
              if [ $countdown -eq 0 ]; then
                if [ "$force" = "1" ]; then
                  echo -ne "\nKill timed out, using kill -9 on $pid... "
                  kill -9 $pid
                  sleep 0.5
                fi
                break
              else
                countdown=$(( $countdown - 1 ))
              fi
            fi
          done
          if [ -e /proc/$pid ]; then
            echo "Timed Out"
          else
            echo "Stopped"
          fi
        else
          echo "Process $pid is not running"
        fi

        rm -f $pidfile
      else
        echo "Pidfile $pidfile doesn't exist"
      fi
    }
    '''
    pass

@hooks.hook('db-relation-changed')
def db_relation_changed():
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
    '''
    os.environ['CONFIG_DIR=/var/lib/cloudfoundry/cfcloudcontroller/jobs/config
    os.environ['CLOUD_CONTROLLER_NG_CONFIG=$CONFIG_DIR/cloud_controller_ng.yml
    os.environ['CC_DIR=/var/lib/cloudfoundry/cfcloudcontroller

    NATS_RUN_DIR=/var/vcap/sys/run/nats
    NATS_LOG_DIR=/var/vcap/sys/log/nats

    mkdir -p $NATS_RUN_DIR
    mkdir -p $NATS_LOG_DIR


    NATS_CONFIG="$CONFIG_DIR/nats.yml"

    cat <<EOF > $NATS_CONFIG
    ---
    net: `relation-get private-address`
    port: 4222

    pid_file: $NATS_RUN_DIR/nats.pid
    log_file: $NATS_LOG_DIR/nats.log

    authorization:
      user: admin
      password: "password"
      timeout: 5
    EOF

    cd $CC_DIR

    juju-log "Starting NATS server..."

    exec bundle exec nats-server -c /var/lib/cloudfoundry/cfcloudcontroller/jobs/config/nats.yml -d
    '''


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

