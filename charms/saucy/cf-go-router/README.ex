# Overview

This charm provides the Cloud Foundry [Router](https://github.com/cloudfoundry/gorouter).

The Router routes traffic coming into Cloud Foundry to the appropriate component – usually Cloud Controller or an application running on a DEA node.
The router is implemented in Go. Routers listen for the messages that a DEA issues when an application comes online or goes offline, and maintain an in-memory routing table.
Incoming requests are load balanced across a pool of Routers.

# Usage

To deploy the Cloud Controller service:

    juju deploy cf-go-router

## Known Limitations and Issues

There are no known limitations.
