import os
import string
import random
import yaml

from charmhelpers.core import host


NATS_CONF_PATH = "/etc/nats.yml"


def get_nats_config(nats_conf_path=NATS_CONF_PATH):
    if not os.path.exists(nats_conf_path):
        generate_nats_config(nats_conf_path)
    with open(nats_conf_path) as fh:
        data = yaml.safe_load(fh.read())
    return data


def generate_nats_config(conf_path):
    user = "".join(random.sample(string.letters, 10))
    password = "".join(random.sample(string.letters, 10))
    nats_data = {
        'net': '0.0.0.0',
        'port': 4222,
        'logtime': True,
        'authorization': {
            'user': user,
            'password': password}}
    host.write_file(
        conf_path, yaml.safe_dump(nats_data), perms=0400)
