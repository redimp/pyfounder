#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import sys
import unittest
import tempfile
import requests
import pyfounder.cli as cli
import pyfounder.server
from flask import Flask
from pyfounder.helper import mkdir_p
from click.testing import CliRunner
from flask_testing import LiveServerTestCase
from test_pyfounder import TEST_PXE_INSTALL_BIONIC, TEST_HOSTS_YML

class ClientLiveServerTest(LiveServerTestCase):

    def __init__(self, *args, **kwargs):
        super(ClientLiveServerTest, self).__init__(*args, **kwargs)
        self.tempdir = tempfile.TemporaryDirectory()

    def setUp(self):
        try:
            self.old_ENV_PYFOUNDER_CLIENT_CONFIG = os.environ['PYFOUNDER_CLIENT_CONFIG']
        except KeyError:
            self.old_ENV_PYFOUNDER_CLIENT_CONFIG = ''
        os.environ['PYFOUNDER_CLIENT_CONFIG'] = \
                os.path.join(self.tempdir.name, 'pyfounderclient.yaml')
        self.runner = CliRunner()
        # configure server environment
        pyfounder.server.db.create_all();
        # create directory structure and write config files
        # hosts.yaml
        with open(self.flask_app.config['PYFOUNDER_HOSTS'],'w') as f:
            f.write(TEST_HOSTS_YML)
        # pxe/
        mkdir_p(self.flask_app.config['PXECFG_DIRECTORY'])
        # templates/
        mkdir_p(self.flask_app.config['PYFOUNDER_TEMPLATES'])
        mkdir_p(os.path.join(self.flask_app.config['PYFOUNDER_TEMPLATES'],'pxe'))
        with open(os.path.join(self.flask_app.config['PYFOUNDER_TEMPLATES'],'pxe','install-bionic'),'w') as f:
            f.write(TEST_PXE_INSTALL_BIONIC)

    def tearDown(self):
        # restore environment variable
        os.environ['PYFOUNDER_CLIENT_CONFIG'] = self.old_ENV_PYFOUNDER_CLIENT_CONFIG
        # unconfigure server environment
        pyfounder.server.db.drop_all();

    def __del__(self):
        try:
            self.tempdir.cleanup()
        except FileNotFoundError:
            pass

    def create_app(self):
        # temporary file for testing client configuration
        self.flask_app = pyfounder.server.app
        self.flask_app.config['TESTING'] = True
        self.flask_app.config['DEBUG'] = True
        self.flask_app.config['LIVESERVER_PORT'] = 0
        #self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///{}".format(
        #        os.path.join(self.tempdir.name,'db.sqlite'))
        #print(self.flask_app.config['SQLALCHEMY_DATABASE_URI'])
        pyfounder.server.db.create_all();

        # WARNING: Setting a SERVER_NAME breaks flask-testing
        #self.flask_app.config['SERVER_NAME'] = 'localhost'
        self.flask_app.config['PXECFG_DIRECTORY'] = os.path.join(self.tempdir.name,'pxelinux.cfg')
        self.flask_app.config['PYFOUNDER_HOSTS'] =  os.path.join(self.tempdir.name,'hosts.yaml')
        self.flask_app.config['PYFOUNDER_TEMPLATES'] = os.path.join(self.tempdir.name,'templates')

        # hack to disable flask banner
        flask_cli = sys.modules['flask.cli']
        flask_cli.show_server_banner = lambda *x: None

        self.test_client = self.flask_app.test_client()

        return self.flask_app

    def requests_get(self, query, *args, **kwargs):
        query = query.lstrip("/")
        return requests.get("{}/{}".format(self.get_server_url(),query), *args, **kwargs)

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

class cliTest(ClientLiveServerTest):
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

    def test_command_ls(self):
        self.configure_client()
        result = self.run_founder(["ls"])
        self.assertEqual(result.exit_code, 0)
        # check output
        # header?
        self.assertRegex(result.output,r'hostname\s+mac\s+ip\s+states')
        # host listed?
        self.assertRegex(result.output,r'example1\s+00:11:22:33:44:55\s+10.0.0.2')

    def test_command_ls_wildcard(self):
        self.configure_client()
        result = self.run_founder(["ls","ex%mple1"])
        self.assertEqual(result.exit_code, 0)
        # check output
        #print(result.output)
        # header?
        self.assertRegex(result.output,r'hostname\s+mac\s+ip\s+states')
        # host listed?
        self.assertRegex(result.output,r'example1\s+00:11:22:33:44:55\s+10.0.0.2')


if __name__ == "__main__": 
    unittest.main()
