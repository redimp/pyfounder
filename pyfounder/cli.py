#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import click
import requests
from pyfounder.helper import yaml_load, yaml_dump, mkdir_p, empty_or_None
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
    try:
        timout = cfg['timeout']
    except KeyError:
        timeout = 2.0
    # check version
    if 'version' not in cfg:
        try:
            r = requests.get("{}/version".format(cfg['url']))
        except requests.RequestException as e:
            raise click.UsageError("Failed to check server version: {}".format(e))
        cfg['version'] = r.text
        cfg.save()
    r = requests.get("{}{}".format(cfg['url'], u), timeout=1.0)
    r.raise_for_status()
    return r.text

def query_server_yaml(u):
    try:
        y = query_server(u)
    except requests.exceptions.ConnectionError:
        raise click.ClickException("Unable to connect to the server.")
    return yaml_load(y)

@click.group()
@click.version_option()
@pass_config
def cli(cfg):
    """pyfounder client."""
    cfg.load()

@cli.command()
@click.option('--url', type=str, help='pyfounder server url')
@click.option('--timeout', type=float, help='timeout for server reply')
@pass_config
def client(cfg, url=None, timeout=None):
    """Client configuration"""
    options_used = 0
    if url is not None:
        url = url.rstrip('/')
        cfg['url'] = url
        options_used += 1
    if timeout is not None:
        cfg['timeout'] = timeout
        options_used += 1
    if options_used > 0:
        cfg.save()
    else:
        raise click.UsageError("Missing parameter.")

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
    """List hosts"""
    if hostname is None or len(hostname)<1:
        host_list = query_server_yaml('/api/hosts/')
    else:
        host_list = host_query(hostname)
    # pick data to print
    data = []
    for hd in host_list:
        data.append([hd['name'], hd['mac'], hd['ip'], hd['state']])
    # print data
    click.echo(tabulate(data, headers=['hostname','mac','ip','states']))


@cli.command('show')
@click.argument('hostname', nargs=-1)
def host_show(hostname):
    """Show host detailed information"""
    hostdata = host_query(hostname)
    click.echo(pformat(hostdata))


@cli.command('dnsmasq')
@click.argument('hostname', nargs=-1)
def dnsmasq(hostname):
    """Print dnsmasq configuration"""
    data = host_query(hostname)
    for h in data:
        comment = ''
        # dhcp-host=3c:fd:fe:67:4a:20,node1,10.0.0.1
        if empty_or_None(h['mac']) or empty_or_None(h['name']) or empty_or_None(h['ip']):
            comment = "# "
        click.echo("{}dhcp-host={},{},{}".format(comment, h['mac'] or '?',h['name'] or '?',h['ip'] or '?'))


@cli.command('yaml')
@click.argument('hostname', nargs=-1)
def host_yaml(hostname):
    """Print yaml configuration using discovered and configured data"""
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

def send_api_command(hostname, command, option=None):
    hosts = host_query(hostname)
    if len(hosts)<1:
        click.echo("No matching hosts found.")
    for host in hosts:
        if empty_or_None(host['mac']):
            # print warning
            click.echo("No mac address for {} found.".format(host['name']))
            continue
        u = '/api/{}/{}'.format(command,host['mac'])
        if option is not None:
            u += '/' + option
        reply = query_server(u)
        click.echo('{} replied {}'.format(host['name'] or host['mac'],reply))

@cli.command('rediscover')
@click.argument('hostname', nargs=-1)
def host_rediscover(hostname):
    """Ask the host to rediscover"""
    return send_api_command(hostname, 'rediscover')

@cli.command('remove')
@click.argument('hostname', nargs=-1)
def host_remove(hostname):
    """Remove the host from the database and remove all config files"""
    return send_api_command(hostname, 'remove')

@cli.command('install')
@click.argument('hostname', nargs=-1)
@click.option('--force', '-f', is_flag=True, help="Force installation.")
def host_install(hostname, force):
    """Install the host"""
    return send_api_command(hostname, 'install', 'force' if force else None)

@cli.command('rebuild')
@click.argument('hostname', nargs=-1)
def host_rebuild(hostname):
    """Install the host"""
    return send_api_command(hostname, 'rebuild')

if __name__ == "__main__":
    cli()
