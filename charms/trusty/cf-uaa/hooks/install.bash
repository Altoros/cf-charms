#!/bin/bash

set -xe

apt-add-repository ppa:cf-charm/ppa && apt-get update
apt-get install -y cfuaa cfuaajob cfregistrar

# Is it installed and running by default? Uninstall it if necessary
juju-log "Stopping Tomcat ..."
/etc/init.d/tomcat7 stop

juju-log "Installing SQLite jdbc driver jar into Tomcat lib directory ..."
cd /var/lib/cloudfoundry/cfuaa/tomcat/lib/
if [ ! -f sqlite-jdbc-3.7.2.jar ]; then
    wget https://bitbucket.org/xerial/sqlite-jdbc/downloads/sqlite-jdbc-3.7.2.jar
fi

juju-log "Creating log directory ..."
mkdir -p /var/log/cloudfoundry/uaa

juju-log "Cleaning up old config files ..."
rm -rf /var/lib/cloudfoundry/cfuaa/jobs/config/*
