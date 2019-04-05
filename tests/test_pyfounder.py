#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import unittest
import tempfile

import pyfounder
from pyfounder.helper import mkdir_p

TEST_HOSTS_YML = """---
globals:

hosts:
  example1:
    interface: enp0s8
    mac: 00:11:22:33:44:55
    ip: 10.0.0.2
    class: workstation

classes:
  default: 
    templates: &default_temlates
      pxelinux.cfg: pxe/install-bionic
      preseed.cfg: pressed.cfg/default
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


class TestApp(object):
    def __init__(self):
        self.app = pyfounder.app
        self._test_client = self.app.test_client()
        self.tempdir = tempfile.TemporaryDirectory()
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

    def __del__(self):
        self.tempdir.cleanup()

    def test_client(self):
        return self._test_client

class PyfounderTestCaseBase(unittest.TestCase):
    def setUp(self):
        self.app = TestApp()
        self.test_client = self.app.test_client()

class ConfigTest(PyfounderTestCaseBase):
    def test_config(self):
        rv = self.test_client.get('/config')
        response = rv.data.decode()
        self.assertIn('PYFOUNDER_HOSTS', response)
        self.assertIn('PYFOUNDER_TEMPLATES', response)
        self.assertIn('PXECFG_DIRECTORY', response)

    def test_host_config(self):
        rv = self.test_client.get('/fetch/example1/pxelinux.cfg',
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

    def test_fetch_discovert(self):
        rv = self.test_client.get('/fetch-discovery')
        response = rv.data.decode()
        self.assertIn("#!/usr/bin/env python3",response)
        self.assertIn("print(dump(data, Dumper=Dumper))",response)

    def test_discovery_report(self):
        yaml = """cpu_model: testcpu
interface: enp0s8
mac: 00:11:22:33:44:55
ram_bytes: '1024'
serialnumber: '42'
"""
        rv = self.test_client.post('/discovery-report', data=dict(data=yaml))
        response = rv.data.decode()
        self.assertEqual(response, '00:11:22:33:44:55')

if __name__ == '__main__':
    unittest.main()
