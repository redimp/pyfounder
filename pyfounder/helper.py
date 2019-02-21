#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os

class ConfigException(Exception):
    pass

def get_pxecfg_directory():
    from pyfounder import app
    p = app.config['PXECFG_DIRECTORY']
    if not len(p)>0:
        raise ConfigException("Not configured.".format(p))
    if not os.path.isdir(p):
        raise ConfigException("Directory {} not found.".format(p))
    if not os.access(p, os.W_OK):
        raise ConfigException("Directory {} is not writeable.".format(p))
    return p

def get_hosts_yaml():
    from pyfounder import app
    p = app.config['PYFOUNDER_HOSTS']
    if not len(p)>0:
        raise ConfigException("Not configured.".format(p))
    if not os.path.isfile(d):
        raise ConfigException("File {} not found.".format(p))
    if not os.access(p, os.R_OK):
        raise ConfigException("File {} is not readable.".format(p))

def get_template_directory():
    from pyfounder import app
    p = app.config['PXECFG_DIRECTORY']
    if not len(p)>0:
        raise ConfigException("Not configured.".format(p))
    if not os.path.isdir(p):
        raise ConfigException("Directory {} not found.".format(p))
    if not os.access(p, os.W_OK):
        raise ConfigException("Directory {} is not writeable.".format(p))
    return p
