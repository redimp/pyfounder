#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import sys
import unittest
import tempfile
import pyfounder.cli as cli
import pyfounder.server
from flask import Flask
from pyfounder.helper import mkdir_p
from click.testing import CliRunner
from flask_testing import LiveServerTestCase
from test_pyfounder import TEST_PXE_INSTALL_BIONIC, TEST_HOSTS_YML

class unconfigured_cli_Test(LiveServerTestCase):
    def setUp(self):
        try:
            self.old_ENV_PYFOUNDER_CLIENT_CONFIG = os.environ['PYFOUNDER_CLIENT_CONFIG']
        except KeyError:
            self.old_ENV_PYFOUNDER_CLIENT_CONFIG = ''
        os.environ['PYFOUNDER_CLIENT_CONFIG'] = \
                os.path.join(self.tempdir.name, 'pyfounderclient.yaml')
        self.runner = CliRunner()


    def tearDown(self):
        # restore environment variable
        os.environ['PYFOUNDER_CLIENT_CONFIG'] = self.old_ENV_PYFOUNDER_CLIENT_CONFIG
        self.tempdir.cleanup()

    def create_app(self):
        # temporary file for testing client configuration
        self.tempdir = tempfile.TemporaryDirectory()
        self.app = pyfounder.server.app
        self.app.config['TESTING'] = True
        self.app.config['LIVESERVER_PORT'] = 0
        self.app.config['SERVER_NAME'] = 'localhost'
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

        # hack to disable flask banner
        flask_cli = sys.modules['flask.cli']
        flask_cli.show_server_banner = lambda *x: None

        return self.app

    def run_founder(self, args=[]):
        result = self.runner.invoke(cli.cli, args)
        return result

    def configure_client(self):
        # configure client
        result = self.run_founder(["client","--verbose","--url",self.get_server_url()])
        self.assertEqual(result.exit_code, 0)
        # check config
        result = self.run_founder(["client","--verbose"])
        self.assertIn(self.get_server_url(), result.output)
        self.assertEqual(result.exit_code, 0)

    def test_no_args(self):
        result = self.run_founder()
        self.assertIn('Usage: cli [OPTIONS] COMMAND [ARGS]...', result.output)
        self.assertEqual(result.exit_code, 0)

    def test_command_client(self):
        # client has to complain if not configured
        result = self.run_founder(["ls"])
        self.assertIn('Error: No server url. Please configure the pyfounder client.',
                result.output)
        self.assertEqual(result.exit_code, 2)
        result = self.runner.invoke(cli.client, ["--verbose", "--url", self.get_server_url()])
        self.assertEqual(result.exit_code, 0)
        self.configure_client()

    #def test_command_ls(self):
    #    self.configure_client()
    #    result = self.runner.invoke(cli.host_list)
    #    print(result.output)
    #    self.assertEqual(result.exit_code, 2)
