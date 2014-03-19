CF Charms helpers
===

Description
---
This folder contains python helpers for cf-charms project and utilities to deploy cloud foundry charms.


Utilities
---
`update_helpers.py` - copies all helpers to charms (idea is take from charmshelpers). It can be called from any folder.
`update_hosts.py` - updates `/etc/hosts` for every service machine. It makes `example.net` to resolve with router ip. It should be run from machine bootstraped with juju. Sccript fetches all necessary config from `juju status` command.
