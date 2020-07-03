#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
from pyfounder.server import db
from pyfounder import helper
from pprint import pformat, pprint
from datetime import datetime

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
        self.in_config_file = False
        self.in_database = False
        if name is not None:
            self.data['name'] = name
        if _dict is not None:
            self.in_config_file = True
            self.from_dict(_dict)
        if _model is not None:
            self.in_database = True
            self.from_db(_model)

    def __repr__(self):
        return "<Host {} {}>".format(self.data['name'] or '?', self.data['mac'] or '?')

    def from_db(self, row):
        """Update Host from db model object"""
        for column in row.__table__.columns:
            value = getattr(row, column.name)
            if column.name not in self.data or value is not None:
                self.data[column.name] = value

    def from_dict(self, d):
        self.data.update(d)
        if self.data['mac'] is not None:
            self.data['mac'] = self.data['mac'].lower()

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
        return os.path.join(helper.get_pxecfg_directory(), fn.lower())

    def write_pxelinux_cfg(self, content):
        fn = self.__pxelinux_cfg_filename()
        with open(fn, 'w') as f:
            f.write(content)

    def remove_pxelinux_cfg(self):
        fn = self.__pxelinux_cfg_filename()
        if not os.path.exists(fn):
            return
        os.remove(fn)

    def update_pxelinux_cfg(self, task=None):
        if task in ['default', 'local']:
            pxe_config = helper.fetch_template('pxelinux.cfg', self.data['name'])
            self.write_pxelinux_cfg(pxe_config)
        elif task == 'install':
            pxe_config = helper.fetch_template('pxelinux.cfg-install', self.data['name'])
            self.write_pxelinux_cfg(pxe_config)
        else:
            raise RuntimeError("write_pxelinux_cfg: unknown task {}".format(task))

    def update_boot_cfg(self):
        hi = self.get_hostinfo()
        if hi is None:
            # remove pxe config, host should boot into default == discovery
            self.remove_pxelinux_cfg()
        if hi.has_state("boot-local") or hi.has_state("installed"):
            self.update_pxelinux_cfg("default")
        elif hi.has_state("boot-install"):
            self.update_pxelinux_cfg("install")
        else:
            self.remove_pxelinux_cfg()

    def remove_boot_cfg(self):
        self.remove_pxelinux_cfg()

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

    def get_hostinfo(self, create_if_not_exists=True):
        self.__assert_mac()
        from pyfounder.models import HostInfo
        host_info = HostInfo.query.filter_by(mac=self.data['mac']).first()
        if host_info is None:
            if not create_if_not_exists:
                return None
            # create host_info
            host_info = HostInfo(mac=self.data['mac'])
            # add infos if available
            now = datetime.utcnow()
            host_info.first_seen = now
            host_info.last_seen = now
            db.session.add(host_info)
            db.session.commit()
        # TODO I don't know why this looks weird to me ...
        if not helper.empty_or_None(self.data['name']):
            host_info.name = self.data['name']
            db.session.add(host_info)
            db.session.commit()
        return host_info

    def enter_state(self, state):
        hi = self.get_hostinfo()
        # handle all the install states:
        installer_states = ["early_command","early_command_done","reboot_into_preseed",
                    "booting_into_preseed",
                    "late_command","late_command_done","first_boot","first_boot_done",
                    "installed"]
        if state in installer_states:
            # clear old state
            for s in installer_states:
                hi.remove_state(s)
            # set new state
            hi.add_state(state)
        if state == "reboot_into_preseed":
            hi.add_state("boot-install")
            hi.remove_state("boot-local")
            self.update_boot_cfg()
        if state in ["late_command_done", "reboot_out_preseed", "installed"]:
            hi.add_state("boot-local")
            hi.remove_state("boot-install")
            self.update_boot_cfg()
        if state == "first_boot_done":
            hi.remove_state("first_boot_done")
            hi.add_state("installed")
        db.session.add(hi)
        db.session.commit()

def get_host(mac):
    """
    returns a host object if the host is either found in the database (was discovered)
    or was configured.
    """
    host_config = None
    # load configuration of all hosts
    hosts_config = helper.load_hosts_config()
    # check if the mac is found in the configuration
    n = helper.find_hostname_by_mac(mac,hosts_config)
    if n is not None:
        host_config = hosts_config[n]
    # check database
    from pyfounder.models import HostInfo
    # check for any discovery info
    query = HostInfo.query.filter_by(mac=mac.lower()).first()
    # no config or discovery data found?
    if query is None and host_config is None:
        return None
    # create and return Host object
    host = Host(_model = query, _dict=host_config)
    return host

