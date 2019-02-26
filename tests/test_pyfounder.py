#!/usr/bin/env python
import os
import unittest
import tempfile

import pyfounder

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class PyfounderTestCase(unittest.TestCase):

    def setUp(self):
        self.app = pyfounder.app
        self.test_client = self.app.test_client()
        self.tempdir = tempfile.TemporaryDirectory()
        self.app.config['SERVER_NAME'] = 'localhost.localdomain'
        self.app.config['PXECFG_DIRECTORY'] = os.path.join(self.tempdir.name,'pxelinux.cfg')
        mkdir_p(self.app.config['PXECFG_DIRECTORY'])
        self.app.config['PYFOUNDER_HOSTS'] =  os.path.join(self.tempdir.name,'hosts.yaml')
        self.app.config['PYFOUNDER_TEMPLATES'] = os.path.join(self.tempdir.name,'templates')
        mkdir_p(self.app.config['PYFOUNDER_TEMPLATES'])



    def tearDown(self):
        self.tempdir.cleanup()

    def test_config(self):
        rv = self.test_client.get('/config')
        response = rv.data.decode()
        self.assertIn('PYFOUNDER_HOSTS', response)
        self.assertIn('PYFOUNDER_TEMPLATES', response)
        self.assertIn('PXECFG_DIRECTORY', response)

if __name__ == '__main__':
    unittest.main()
