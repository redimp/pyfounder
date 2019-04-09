#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import click
import requests
from pyfounder.helper import yaml_load, yaml_dump, mkdir_p

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
    print(cfg)
    # check if url exists
    # check version
    return u

@click.group()
@click.version_option()
@pass_config
def cli(cfg):
    """pyfounder client."""
    cfg.load()

@cli.command()
@click.option('--url', type=str, help='pyfounder server url')
@pass_config
def config(cfg, url=None):
    """Client configuration"""
    if url is not None:
        cfg['url'] = url
    cfg.save()

@cli.group()
def hosts():
    """Manages hosts"""
    pass

@hosts.command('ls')
def host_list():
    click.echo('Host list {}'.format(query_server('x')))

@hosts.command('new')
def host_add():
    click.echo('add Host')

if __name__ == "__main__":
    cli()
