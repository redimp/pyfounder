#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import click
import requests
from pyfounder.helper import yaml_load, yaml_dump, mkdir_p
from pyfounder import __version__
from pprint import pformat, pprint
from tabulate import tabulate

class Config(dict):
    def __init__(self, *args, **kwargs):
        self.config_dir = click.get_app_dir('pyfounder')
        self.config_file = os.path.join(self.config_dir, 'config.yaml')

        super(Config, self).__init__(*args, **kwargs)

    def load(self):
        """load a config file from disk"""
        try:
            with open(self.config_file,'r') as f:
                self.update(yaml_load(f.read()))
        except FileNotFoundError:
            pass

    def save(self):
        mkdir_p(self.config_dir)
        with open(self.config_file,'w') as f:
            f.write(yaml_dump(self))

pass_config = click.make_pass_decorator(Config, ensure=True)

@pass_config
def query_server(cfg,u):
    # check if url exists
    if 'url' not in cfg:
        raise click.UsageError("No server url. Please configure pyfounder.")
    # check version
    if 'version' not in cfg:
        try:
            r = requests.get("{}/version".format(cfg['url']))
        except requests.RequestException as e:
            raise click.UsageError("Failed to check server version: {}".format(e))
        cfg['version'] = r.text
        cfg.save()
    r = requests.get("{}{}".format(cfg['url'], u))
    r.raise_for_status()
    return r.text

def query_server_yaml(u):
    y = query_server(u)
    return yaml_load(y)

@click.group()
@click.version_option()
@pass_config
def cli(cfg):
    """pyfounder client."""
    cfg.load()

@cli.command()
@click.option('--url', type=str, help='pyfounder server url')
@pass_config
def client(cfg, url=None):
    """Client configuration"""
    if url is not None:
        url = url.rstrip('/')
        cfg['url'] = url
    cfg.save()

def host_query(hostname):
    """query hostdata from server - helper function"""
    data = []
    for h in hostname:
        # get list of hostdata
        hostdata = query_server_yaml('/api/hosts/{}'.format(h))
        data += hostdata
    return data

@cli.command('ls')
@click.argument('hostname', nargs=-1)
def host_list(hostname=None):
    if hostname is None or len(hostname)<1:
        host_list = query_server_yaml('/api/hosts/')
    else:
        host_list = host_query(hostname)
    data = []
    for hd in host_list:
        data.append([hd['name'], hd['mac'], hd['ip'], hd['state']])
    click.echo(tabulate(data, headers=['hostname','mac','ip','states']))


@cli.command('show')
@click.argument('hostname', nargs=-1)
def host_show(hostname):
    hostdata = host_query(hostname)

@cli.command('yaml')
@click.argument('hostname', nargs=-1)
def host_yaml(hostname):
    data = host_query(hostname)
    if len(data)>0:
        hosts = {}
        for host in data:
            hosts[host['name']] = {
                    'interface':host['interface'],
                    'mac':host['mac'],
                    'ip':host['ip'],
                    'class':host['class'] or []
                    }
        click.echo(yaml_dump({'hosts':hosts}))

if __name__ == "__main__":
    cli()
