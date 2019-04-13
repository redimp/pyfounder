#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
from pyfounder import db, helper
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

    def __repr__(self):
        return "<Host {} {}>".format(self.data['name'] or '?', self.data['mac'] or '?')

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

    def __assert_mac(self):
        if helper.empty_or_None(self.data['mac']):
            raise ValueError('No mac address configured.')

    def __pxelinux_cfg_filename(self):
        self.__assert_mac()
        fn = "01-{}".format(self.data['mac'].replace(":","-"))
        return os.path.join(helper.get_pxecfg_directory(), fn)

    def update_pxelinux_cfg(self, content):
        fn = self.__pxelinux_cfg_filename()
        with open(fn, 'w') as f:
            f.write(content)

    def remove_pxelinux_cfg(self):
        fn = self.__pxelinux_cfg_filename()
        if not os.path.exists(fn):
            return
        os.remove(fn)

    def send_command(self, command, add_state=None, remove_state=None):
        self.__assert_mac()
        from pyfounder.models import HostCommand
        # clear old commands
        HostCommand.query.filter_by(mac=self.data['mac']).delete()
        # add new command
        cmd = HostCommand(mac=self.data['mac'],
                command=command,
                add_state=add_state,
                remove_state=remove_state)
        db.session.add(cmd)
        db.session.commit()

    def get_hostinfo(self):
        self.__assert_mac()
        from pyfounder.models import HostInfo
        return HostInfo.query.filter_by(mac=self.data['mac']).first()

