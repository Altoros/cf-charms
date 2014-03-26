Bundles of Juju Charms for Cloud Foundry
=========

# Overview

Single node setup using Ubuntu 14.04 to be used for testing and product evaluation.
* Charms that will be part of the CF bundle:
    - Cloud Controller
    - NATS (ruby)
    - DEA
    - Go Router
    - UAA

Every charm depend on one or more package. Packages are available on https://launchpad.net/~cf-charm/+archive/ppa/+packages

# Releases
## P0 (Free Download)
* Builds to be used:
    - Cloud Foundry: cf-147 or the latest suitable release.
    - Ubuntu Release: 14.04
* Installation and Deployment Modes
    - Single Node
        - Juju Deploy CF on Ubuntu running in bare metal on a single machine.
        - Configuration: Minimum 8GB RAM

    - Multi Node
        - Juju Deploy OpenStack and CF on a set of hosts.
        - Use MAAS to provision the hosts with Ubuntu and KVM.
        - No HA
* Other Capabilities
    - Service Brokers
        - Service Broker for MYSQL only. To be deployed using Juju.
        - UPI Support - the ability to find software that is running elsewhere. (UPI - User Provided Instance)
* Support
    - No support


# Deploying with juju deployer

```
sudo pip install juju-deployer
export JUJU_REPOSITORY=/path/to/charms/directory
juju set-constraints "arch=amd64"
juju deployer -vdWc cloudfoundry.yml # v = verbose, d = debug, W = watch, c = configs (the yaml file)
```

