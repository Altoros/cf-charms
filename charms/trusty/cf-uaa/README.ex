This charm install CloudFoundry User Account and Authentication (UAA) Server
https://github.com/cloudfoundry/uaa

Overview
--------

The UAA is the identity management service for Cloud Foundry.
It's primary role is as an OAuth2 provider, issuing tokens for client applications to use when they act on behalf of Cloud Foundry users.
It can also authenticate users with their Cloud Foundry credentials, and can act as an SSO service using those credentials (or others).
It has endpoints for managing user accounts and for registering OAuth2 clients, as well as various other management functions.


Usage
-----

Step by step instructions on using the charm:

    juju deploy uaa

#ToDo: complete

You can then browse to http://ip-address to configure the service. 

Configuration
#ToDo: complete

The configuration options will be listed on the charm store, however If you're making assumptions or opinionated decisions in the charm (like setting a default administrator password), you should detail that here so the user knows how to change it immediately, etc.


Contact Information
-------------------
#ToDo: complete

Though this will be listed in the charm store itself don't assume a user will know that, so include that information here:

Author:
Report bugs at: http://bugs.launchpad.net/charms/+source/charmname
Location: http://jujucharms.com/charms/distro/charmname

* Be sure to remove the templated parts before submitting to https://launchpad.net/charms for inclusion in the charm store.

