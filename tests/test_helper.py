#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import tempfile
import unittest

import pyfounder.helper

class mkdir_p_Test(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_mkdir_p(self):
        path_a = os.path.join(self.tempdir.name,'a')
        path_a_b = os.path.join(self.tempdir.name,'a','b')
        # create directory
        pyfounder.helper.mkdir_p(path_a)
        # this must not throw an exception
        pyfounder.helper.mkdir_p(path_a)
        # the directory mus exist
        self.assertTrue(os.path.exists(path_a))
        # create a sub directory
        pyfounder.helper.mkdir_p(path_a_b)

class yaml_Test(unittest.TestCase):
    def test_yaml_load(self):
        data = pyfounder.helper.yaml_load("")
        self.assertIsNone(data)
        data = pyfounder.helper.yaml_load("""
a:
    - b
    - c
        """)
        self.assertEqual(data,{'a': ['b', 'c']})

    def test_yaml_dump(self):
        d = {'a': ['b', 'c']}
        y = pyfounder.helper.yaml_dump(d)
        self.assertEqual(d,pyfounder.helper.yaml_load(y))

if __name__ == '__main__':
    unittest.main()
