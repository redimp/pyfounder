#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import unittest
import tempfile

from test_pyfounder import PyfounderTestCaseBase

class TestHostInfoModel(PyfounderTestCaseBase):
    def test_state(self):
        from pyfounder import models
        host = models.HostInfo(name='testie')
        self.assertEqual(host.get_states(), [])
        self.assertFalse(host.has_state('a'))
        host.add_state('a')
        self.assertEqual(host.get_states(), ['a'])
        host.add_state('b','c','d')
        self.assertEqual(sorted(host.get_states()), sorted(['a','b','c','d']))
        self.assertTrue(host.has_state('a'))
        self.assertTrue(host.has_state('d'))
        host.remove_state('a','b','c')
        self.assertFalse(host.has_state('a'))
        self.assertTrue(host.has_state('d'))
        host.remove_state('a')


if __name__ == '__main__':
    unittest.main()
