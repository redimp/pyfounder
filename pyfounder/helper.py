#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import errno
import fnmatch

import yaml
try:
        from yaml import CLoader as yaml_Loader, CDumper as yaml_Dumper
except ImportError:
        from yaml import Loader as yaml_Loader, Dumper as yaml_Dumper

class ConfigException(Exception):
    pass

def yaml_load(str):
    return yaml.load(str, Loader=yaml_Loader)

def yaml_dump(data):
    return yaml.dump(data, Dumper=yaml_Dumper)

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
            return yaml.load(f, Loader=yaml_Loader)
    except (yaml.MarkedYAMLError) as e:
        raise ConfigException("Unable to load {}: {}.".format(filename,e))
    except (IOError, yaml.YAMLError) as e:
        raise ConfigException("Unable to load {}: {}.".format(filename,e))

_host_default_data = {
    'name':None,
    'mac':None,
    'ip':None,
    'interface':None,
    'class':None,
    'states':[],
}

def load_hosts_config(filename=None):
    d = load_hosts_yaml(filename)
    hosts = {}
    if 'hosts' not in d or d['hosts'] is None:
        return {}
    for hostname, cfg in d['hosts'].items():
        # set host default values
        hosts[hostname] = _host_default_data
        if 'class' in cfg:
            if cfg['class'] in d['classes']:
                hosts[hostname] = d['classes'][cfg['class']]
        for key,value in cfg.items():
            hosts[hostname][key] = value
        # that looks strange, but it necessary to get everything
        # in one place, when generating the templates
        hosts[hostname]['name'] = hostname
    return hosts

def host_config(hostname, hosts):
    if hosts is None:
        hosts = load_hosts_config()
    return hosts[hostname]

def find_hostname_by_mac(mac, hosts=None):
    if hosts is None:
        hosts = load_hosts_config()
    for name,config in hosts.items():
        if config['mac'] == mac:
            return name
    return None

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def configured_template(template_file, cfg={}):
    # load the jinja stuff
    from jinja2 import FileSystemLoader, Environment
    from jinja2.exceptions import TemplateNotFound
    # create context
    context = cfg
    for key, value in cfg['variables'].items():
        context[key] = value
    # FIXME: should env be global?
    env = Environment(
            loader=FileSystemLoader(get_template_directory()))
    try:
        # load template
        template = env.get_template(template_file)
    except TemplateNotFound as e:
        abort(404, "Template {} not found.".format(template_file))
    # render
    rendered_content = template.render(**context)
    return rendered_content

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = getattr(row, column.name)
    return d


def empty_or_None(s):
    if s is None:
        return True
    if len(s.strip())<1:
        return True
    return False


def config_host_data(_hostdata, hosts_config=None):
    result = []
    if hosts_config is None:
       hosts_config = load_hosts_config()
    for _host in _hostdata:
        host = dict(_host_default_data)
        host.update(_host)
        _hc = None
        if not empty_or_None(host['mac']):
            _hn = find_hostname_by_mac(host['mac'],hosts_config)
            _hc = hosts_config[_hn]
        if _hc is None and host['name'] in hosts_config:
            _hc = hosts_config[host['name']]
        if _hc is not None:
            host.update(_hc)
        result.append(host)
    return result


def fnmatch2sql(pattern):
    return pattern
