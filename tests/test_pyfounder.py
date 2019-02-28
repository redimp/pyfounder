#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import unittest
import tempfile

import pyfounder
from pyfounder.helper import mkdir_p

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

    def __del__(self):
        self.tempdir.cleanup()

    def test_client(self):
        return self._test_client

class PyfounderTestCase(unittest.TestCase):

    def setUp(self):
        self.app = TestApp()
        self.test_client = self.app.test_client()

    def test_config(self):
        rv = self.test_client.get('/config')
        response = rv.data.decode()
        self.assertIn('PYFOUNDER_HOSTS', response)
        self.assertIn('PYFOUNDER_TEMPLATES', response)
        self.assertIn('PXECFG_DIRECTORY', response)

if __name__ == '__main__':
    unittest.main()
