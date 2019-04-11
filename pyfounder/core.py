#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from pprint import pformat, pprint

class Host:
    def __init__(self, name=None, _model=None, _dict=None):
        # default values
        self.data = {
            'name' : None,
            'mac' : None,
            'ip' : None,
            'interface' : None,
            'class' : None,
            'state' : '',
        }
        if name is not None:
            self.data['name'] = name
        if _model is not None:
            self.from_db(_model)
        if _dict is not None:
            self.from_dict(_dict)

    def from_db(self, row):
        """Update Host from db model object"""
        for column in row.__table__.columns:
            self.data[column.name] = getattr(row, column.name)

    def from_dict(self, d):
        self.data.update(d)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]
