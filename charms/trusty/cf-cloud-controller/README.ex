# Overview

This charm provides the Cloud Foundry [Cloud Controller](https://github.com/cloudfoundry/cloud_controller_ng).

Cloud Controller (CC) is the Cloud Foundry component that orchestrates the processing performed by backend components, such as application staging and lifecycle management, and service provisioning and binding operations. Cloud Controller functions and features include:

- Maintenance of a database of information about applications, services, and configurable items such as organizations, spaces, users, and roles.
- Storage of application packages and droplets in the blobstore.
- Interaction, via the NATS messaging bus, with other Cloud Foundry components, including Droplet Execution Agents (DEAs), Service Gateways, and the Health Manager.
- A REST API that enables client access to backend functionality.

# Usage

To deploy the Cloud Controller service:

    juju deploy cf-cloud-controller

## Known Limitations and Issues

There are no known limitations.
