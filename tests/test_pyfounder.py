#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import unittest
import tempfile

import pyfounder
import pyfounder.server
from pyfounder.helper import mkdir_p
from pyfounder.core import get_host

TEST_HOSTS_YML = """---
globals:

hosts:
  example1:
    interface: enp0s8
    mac: 00:11:22:33:aa:55
    ip: 10.0.0.2
    class: workstation

classes:
  default:
    templates: &default_temlates
      pxelinux.cfg: pxe/boot-local
      pxelinux.cfg-install: pxe/install-bionic
      preseed.cfg: pressed.cfg/default
      test-snippets: test-snippets
    variables: &default_variables
      test: one
      locale: en_US.UTF-8
  # the class for all workstations
  workstation: &workstation
    templates:
      <<: *default_temlates
    variables:
      <<: *default_variables
      test: two
"""

TEST_PXE_INSTALL_BIONIC = """default install
timeout 0

LABEL install
        kernel bionic/ubuntu-installer/amd64/linux
        append vga=normal initrd=bionic/ubuntu-installer/amd64/initrd.gz locale={{locale}} debian-installer/keymap=us pkgsel/install-language-support=false netcfg/dhcp_timeout=120 console-setup/layoutcode=us console-setup/ask_detect=false netcfg/choose_interface={{interface}}
"""

TEST_SNIPPETS = """
wget -q -O /dev/null {{pyfounder_url}}/report/state/{{mac}}/early_command
"""


class TestApp(object):
    def __init__(self):
        self.app = pyfounder.server.app
        self._test_client = self.app.test_client()
        self.tempdir = tempfile.TemporaryDirectory()
        self.app.config['PYFOUNDER_URL'] = "http://127.0.0.1:5000"
        self.app.config['SERVER_NAME'] = 'localhost.localdomain'
        self.app.config['PXECFG_DIRECTORY'] = os.path.join(self.tempdir.name,'pxelinux.cfg')
        mkdir_p(self.app.config['PXECFG_DIRECTORY'])
        self.app.config['PYFOUNDER_HOSTS'] =  os.path.join(self.tempdir.name,'hosts.yaml')
        self.app.config['PYFOUNDER_TEMPLATES'] = os.path.join(self.tempdir.name,'templates')
        mkdir_p(self.app.config['PYFOUNDER_TEMPLATES'])
        # write files
        mkdir_p(os.path.join(self.app.config['PYFOUNDER_TEMPLATES'],'pxe'))
        with open(os.path.join(self.app.config['PYFOUNDER_TEMPLATES'],'pxe','install-bionic'),'w') as f:
            f.write(TEST_PXE_INSTALL_BIONIC)
        with open(self.app.config['PYFOUNDER_HOSTS'],'w') as f:
            f.write(TEST_HOSTS_YML)
        with open(os.path.join(self.app.config['PYFOUNDER_TEMPLATES'],'test-snippets'),'w') as f:
            f.write(TEST_SNIPPETS)

    def __del__(self):
        self.tempdir.cleanup()

    def test_client(self):
        return self._test_client

class PyfounderTestCaseBase(unittest.TestCase):
    def setUp(self):
        self.app = TestApp()
        self.test_client = self.app.test_client()
        pyfounder.server.db.create_all()

    def tearDown(self):
        pyfounder.server.db.drop_all()

class ConfigTest(PyfounderTestCaseBase):
    def test_config(self):
        rv = self.test_client.get('/config')
        response = rv.data.decode()
        self.assertIn('PYFOUNDER_HOSTS', response)
        self.assertIn('PYFOUNDER_TEMPLATES', response)
        self.assertIn('PXECFG_DIRECTORY', response)

    def test_host_config(self):
        rv = self.test_client.get('/fetch/example1/pxelinux.cfg-install',
                follow_redirects=True)
        response = rv.data.decode()
        # test simple variable
        self.assertIn('netcfg/choose_interface=enp0s8', response)
        # test variable from inherited class
        self.assertIn('locale=en_US.UTF-8', response)

class DiscoverTest(PyfounderTestCaseBase):
    def test_version(self):
        rv = self.test_client.get('/version')
        response = rv.data.decode()
        self.assertRegex(response, r'pyfounder \d+\.\d+.*')

    def test_fetch_discovery(self):
        rv = self.test_client.get('/fetch-discovery')
        response = rv.data.decode()
        self.assertIn("#!/usr/bin/env python3",response)
        self.assertIn("print(dump(data, Dumper=Dumper))",response)

    def _discovery_testhost(self, mac):
        yaml = "cpu_model: testcpu\ninterface: enp0s8\n"+\
               "mac: {}\nram_bytes: '1024'\nserialnumber: '42'\n".format(mac)
        rv = self.test_client.post('/discovery-report', data=dict(data=yaml))
        response = rv.data.decode()
        self.assertEqual(response, mac)

    def test_discovery_report(self):
        mac = '99:88:77:66:55:aa'
        self._discovery_testhost(mac)
        # test receiving empty command
        rv = self.test_client.get('/discovery-remote-control/{}'.format(mac))
        response = rv.data.decode()
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(response,'wait')

    def test_remote_unknown_host(self):
        mac = '99:88:77:66:55:aa'
        rv = self.test_client.get('/discovery-remote-control/{}'.format(mac))
        response = rv.data.decode()
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Host not found.', response)
        # TODO check log
        # see https://testfixtures.readthedocs.io/en/latest/logging.html#the-decorator

    def test_receive_send_command_discovered_host(self):
        mac = '99:88:77:66:55:aa'
        self._discovery_testhost(mac)
        h = get_host(mac)
        # send test command
        cmd = 'xxxaaa'
        h.send_command(cmd)
        # receive test command
        rv = self.test_client.get('/discovery-remote-control/{}'.format(mac))
        response = rv.data.decode()
        self.assertEqual(response, cmd)
        # receive wait command
        rv = self.test_client.get('/discovery-remote-control/{}'.format(mac))
        response = rv.data.decode()
        self.assertEqual(response, 'wait')

    def test_receive_send_command_configured_host(self):
        host_config = pyfounder.helper.host_config("example1")
        mac = host_config['mac']
        h = get_host(mac)
        cmd = 'xxxaaa'
        h.send_command(cmd)
        rv = self.test_client.get('/discovery-remote-control/{}'.format(mac))
        response = rv.data.decode()
        self.assertEqual(response, cmd)
        rv = self.test_client.get('/discovery-remote-control/{}'.format(mac))
        response = rv.data.decode()
        self.assertEqual(response, 'wait')

class SnippetTest(PyfounderTestCaseBase):
    def test_status_update(self):
        rv = self.test_client.get('/fetch/example1/test-snippets',
                follow_redirects=True)
        response = rv.data.decode()
        # check for wget option
        self.assertIn('wget -q -O /dev/null http://127.0.0.1:5000/report/state/00:11:22:33:aa:55/early_command',response)


if __name__ == '__main__':
    unittest.main()
