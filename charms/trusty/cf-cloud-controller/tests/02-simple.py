import os
import amulet
import requests

d = amulet.Deployment()
d.add('cf-cloudcontroller', charm='/var/jenkins/cf-charms/charms/trusty/cf-cloudcontroller')

try:
    d.setup(timeout=900)
    d.sentry.wait()
except amulet.helpers.TimeoutError:
    amulet.raise_status(amulet.SKIP, msg="Environment wasn't stood up in time")
except:
    raise
ccl_unit = d.sentry.unit['cf-cloudcontroller']
