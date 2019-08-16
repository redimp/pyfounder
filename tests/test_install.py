#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import sys
import unittest
import requests
import pyfounder.helper
from test_pyfounder import TEST_PXE_INSTALL_BIONIC, TEST_HOSTS_YML
from test_cli import ClientLiveServerTest

EXAMPLE1_DISCOVERY = """
cpu_model: Intel(R) Core(TM) i7-7700 CPU @ 3.60GHz
interface: enp0s31f6
lsblk:
  sda:
  - 133.7G
  - ssd
lshw:
  capabilities:
    smp: Symmetric Multi-Processing
lspci: |-
  00:00.0 Host bridge: Intel Corporation Xeon E3-1200
mac: 00:11:22:33:44:55
ram_bytes: 16706387968
serialnumber: '1234567890'
"""

TEST_PXE_LOCAL_BOOT = """DEFAULT localboot
LABEL localboot
MENU LABEL Boot Local HDD
LOCALBOOT  0"""


class InstallTest(ClientLiveServerTest):

    def test_install_process(self):
        self.configure_client()
        # store pxe local boot template
        with open(os.path.join(self.flask_app.config['PYFOUNDER_TEMPLATES']
                ,'pxe','boot-local'),'w') as f:
            f.write(TEST_PXE_LOCAL_BOOT)
        with open(self.flask_app.config['PYFOUNDER_HOSTS'],'w') as f:
            f.write(TEST_HOSTS_YML)
        # start with empty hosts file:
        with open(self.flask_app.config['PYFOUNDER_HOSTS'],'w') as f:
            f.write("")
        # check founder ls
        result = self.run_founder(["ls"])
        self.assertRegex(result.output,r'hostname\s+mac\s+ip\s+states')
        self.assertNotIn('example1', result.output)
        # emulate discovery of example1
        response = self.requests_get("/discovery-report", data={ 'data' : EXAMPLE1_DISCOVERY })
        # check response
        self.assertEqual('00:11:22:33:44:55',response.text)
        # check discovery
        result = self.run_founder(["ls", "00:11:22:33:44:55"])
        self.assertRegex(result.output,r'00:11:22:33:44:55\s+discovered')
        # simple yaml check
        result = self.run_founder(["yaml", "00:11:22:33:44:55"])
        self.assertRegex(result.output,r'mac:\s+00:11:22:33:44:55')
        # configure example1 using the hosts file
        with open(self.flask_app.config['PYFOUNDER_HOSTS'],'w') as f:
            f.write(TEST_HOSTS_YML)
        result = self.run_founder(["ls"])
        self.assertRegex(result.output,r'hostname\s+mac\s+ip\s+states')
        # assert example1 listed
        self.assertRegex(result.output,r'example1\s+00:11:22:33:44:55\s+10.0.0.2')
        # check remote control state
        response = self.requests_get("/discovery-remote-control/00:11:22:33:44:55")
        self.assertEqual('wait',response.text)
        # test rediscover
        result = self.run_founder(["rediscover", "00:11:22:33:44:55"])
        response = self.requests_get("/discovery-remote-control/00:11:22:33:44:55")
        self.assertEqual('discover',response.text)#;print(response.text)
        # emulate discovery again
        response = self.requests_get("/discovery-report", data={ 'data' : EXAMPLE1_DISCOVERY })
        # check remote command
        response = self.requests_get("/discovery-remote-control/00:11:22:33:44:55")
        self.assertEqual('wait',response.text)
        # run install command
        result = self.run_founder(["install", "example1"])
        self.assertNotIn('Host is not discovered yet.', result.output)
        self.assertNotIn('No matching hosts found.', result.output)
        self.assertIn('example1 replied send command to reboot into preseed.', result.output)
        # check remote command
        response = self.requests_get("/discovery-remote-control/00:11:22:33:44:55")
        self.assertEqual('reboot',response.text)
        # check pxe file
        example1_pxe_filepath = os.path.join(self.flask_app.config['PXECFG_DIRECTORY'],
            '01-00-11-22-33-44-55')
        with open(example1_pxe_filepath,'r') as f:
            example1_pxe = f.read()
        # enable diff of long strings
        self.maxDiff = None
        # render template for host
        example1_pxe_template = pyfounder.helper.fetch_template('pxelinux.cfg-install', 'example1')
        self.assertEqual(example1_pxe.strip(), example1_pxe_template.strip() )
        # emulate installer steps
        # early command
        response = self.requests_get("/report/state/00:11:22:33:44:55/early_command")
        response.raise_for_status()
        # check if state is shown in the client
        result = self.run_founder(["ls", "example1"])
        # FIXME
        self.assertIn('early_command', result.output)

        response = self.requests_get("/report/state/00:11:22:33:44:55/early_command_done")
        response.raise_for_status()
        # late command
        response = self.requests_get("/report/state/00:11:22:33:44:55/late_command")
        response.raise_for_status()
        response = self.requests_get("/report/state/00:11:22:33:44:55/late_command_done")
        response.raise_for_status()
        # first boot
        response = self.requests_get("/report/state/00:11:22:33:44:55/first_boot")
        response.raise_for_status()
        response = self.requests_get("/report/state/00:11:22:33:44:55/first_boot_done")
        response.raise_for_status()

        result = self.run_founder(["ls", "example1"])

    pass

if __name__ == "__main__": 
    unittest.main()
