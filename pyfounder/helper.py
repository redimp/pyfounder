#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import yaml

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
    if not os.path.isfile(p):
        raise ConfigException("File {} not found.".format(p))
    if not os.access(p, os.R_OK):
        raise ConfigException("File {} is not readable.".format(p))
    return p

def get_template_directory():
    from pyfounder import app
    p = app.config['PYFOUNDER_TEMPLATES']
    if not len(p)>0:
        raise ConfigException("Not configured.".format(p))
    if not os.path.isdir(p):
        raise ConfigException("Directory {} not found.".format(p))
    return p

def load_hosts_yaml(filename=None):
    if filename is None:
        filename = get_hosts_yaml()
    try:
        with open(filename, 'r') as f:
            return yaml.load(f)
    except (yaml.MarkedYAMLError) as e:
        raise ConfigException("Unable to load {}: {}.".format(filename,e))
    except (IOError, yaml.YAMLError) as e:
        raise ConfigException("Unable to load {}: {}.".format(filename,e))

def load_hosts_config(filename=None):
    d = load_hosts_yaml(filename)
    hosts = {}
    for hostname, cfg in d['hosts'].items():
        if 'class' in cfg:
            if cfg['class'] in d['classes']:
                hosts[hostname] = d['classes'][cfg['class']]
        for key,value in cfg.items():
            hosts[hostname][key] = value
        # that looks strange, but it necessary to get everything
        # in one place, when generating the templates
        hosts[hostname]['hostname'] = hostname
    return hosts

def host_config(hostname):
    hosts = load_hosts_config()
    return hosts[hostname]
