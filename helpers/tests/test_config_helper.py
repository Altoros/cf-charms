import tempfile
import os
import unittest

from pkg_resources import resource_filename

from helpers.config_helper import render_template, emit_config

TEMPLATE_DIR = "templates"


def template_dir():
    return resource_filename(__name__, TEMPLATE_DIR)


class TestConfigHelper(unittest.TestCase):
    def test_render_ngnix(self):
        output = render_template('nginx.conf',
                                 dict(nginx_port=12345),
                                 template_dir=template_dir())

        self.assertRegexpMatches(output, 'listen\s+12345')

    def test_render_cloudcontroller_conf(self):
        output = render_template('cloud_controller_ng.yml',
                                 dict(cc_port="8080", domain="example.net"),
                                 template_dir=template_dir())

        self.assertRegexpMatches(output, 'port:\s*8080')
        self.assertRegexpMatches(output,
                                 'srv_api_uri:\s*http://api.example.net')

    def test_emit_config_missing_key(self):
        self.assertFalse(emit_config(['foo', 'bar'],
                                     {'foo': True},
                                     'missing', 'missing'))

    def test_emit_config(self):
        fd, fn = tempfile.mkstemp()
        self.assertTrue(emit_config(['nginx_port'],
                                    dict(nginx_port=12345),
                                    'test.conf',
                                    fn,
                                    template_dir=template_dir()))
        output = open(fn, "r").read()
        self.assertRegexpMatches(output, 'listen\s+12345')
        os.unlink(fn)

if __name__ == '__main__':
    unittest.main()
