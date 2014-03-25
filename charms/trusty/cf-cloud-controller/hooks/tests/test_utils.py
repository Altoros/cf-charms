import re
import unittest

from utils import render_template

TEMPLATE_DIR = "../templates"


class TestUtils(unittest.TestCase):
    def test_render_ngnix(self):
        output = render_template('nginx.conf',
                                 dict(nginx_port=12345),
                                 template_dir=TEMPLATE_DIR)

        self.assertTrue(re.search('listen\s+12345', output))

    def test_render_cloudcontroller_conf(self):
        output = render_template('cloud_controller_ng.yml',
                                 dict(cc_port="8080", domain="example.net"),
                                 template_dir=TEMPLATE_DIR)

        self.assertTrue(re.search('port:\s*8080', output))
        self.assertTrue(re.search(
            'srv_api_uri:\s*http://api.example.net', output))

if __name__ == '__main__':
    unittest.main()
