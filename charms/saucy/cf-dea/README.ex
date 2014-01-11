# Overview

This charm provides the Cloud Foundry [Droplet Execution Agent](https://github.com/cloudfoundry/dea_ng).

The Droplet Execution Agent (DEA) is a process that runs on Cloud Foundry VMs that host applications.
A DEA subscribes to the messages that the Cloud Controller publishes when droplets need to be run.
If the DEA host meets the runtime and RAM requirements of a droplet, the DEA responds to the Cloud Controller's request, receives the droplet, and starts it.
Similarly, a DEA stops an application as requested by the Cloud Controller.
A DEA keeps track of the instances it started and periodically broadcasts messages about their state using NATS.

# Usage

To deploy the Cloud Controller service:

    juju deploy cf-dea

## Known Limitations and Issues

There are no known limitations.
