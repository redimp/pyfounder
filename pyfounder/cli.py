#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import click
import requests
from pyfounder.helper import yaml_load, yaml_dump, mkdir_p, empty_or_None, humanbytes
from pyfounder import __version__
from pprint import pformat, pprint
from tabulate import tabulate

class Config(dict):
    def __init__(self, *args, **kwargs):
        self.config_dir = click.get_app_dir('pyfounder')
        try:
            self.config_file = os.environ['PYFOUNDER_CLIENT_CONFIG']
        except KeyError:
            self.config_file = None
        # TODO check for /etc/pyfounder/client.yaml ?
        if self.config_file is None or self.config_file == "":
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
def query_server_core(cfg,u):
    # check if url exists
    if 'url' not in cfg:
        raise click.UsageError("No server url. Please configure the pyfounder client.")
    try:
        timout = cfg['timeout']
    except KeyError:
        timeout = 2.0
    # check version
    if 'version' not in cfg:
        try:
            r = requests.get("{}/version".format(cfg['url']), timeout=timeout)
        except requests.RequestException as e:
            raise click.UsageError("Failed to check server version: {}".format(e))
        else:
            cfg['version'] = r.text
            cfg.save()
    r = requests.get("{}{}".format(cfg['url'], u), timeout=timeout)
    r.raise_for_status()
    return r.text

def query_server(u):
    try:
        txt = query_server_core(u)
    except requests.exceptions.HTTPError as e:
        raise click.ClickException("{}".format(e))
    except requests.exceptions.ConnectionError:
        raise click.ClickException("Unable to connect to the server.")
    return txt

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
@click.option('--timeout', type=float, help='timeout for server reply')
@click.option('-v', '--verbose', count=True)
@pass_config
def client(cfg, url=None, timeout=None, verbose=0):
    """Client configuration"""
    options_used = 0
    if url is not None:
        url = url.rstrip('/')
        cfg['url'] = url
        options_used += 1
        if verbose > 0:
            click.echo('client url     {}'.format(cfg['url']))
    if timeout is not None:
        cfg['timeout'] = timeout
        options_used += 1
    if options_used > 0:
        cfg.save()
    else:
        #raise click.UsageError("Missing parameter.")
        if verbose > 0:
            click.echo('client config  {}'.format(cfg.config_file))
        try:
            click.echo('client url     {}'.format(cfg['url']))
        except KeyError:
            click.echo('client url     not configured.')
        try:
            click.echo('client timeout {}'.format(cfg['timeout'] or "None"))
        except KeyError:
            pass


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
        states = " ".join(sorted([x for x in hd['state'].split('|')]))
        data.append([hd['name'], hd['mac'], hd['ip'], states])
    # print data
    click.echo(tabulate(data, headers=['hostname','mac','ip','states']))


@cli.command('show')
@click.argument('hostname', nargs=-1)
@click.option('-d', '--debug', count=True)
def host_show(hostname, debug):
    """Show host detailed information"""
    hostdata = host_query(hostname)
    if debug > 1:
        click.echo(pformat(hostdata))
    for host in hostdata:
        if debug > 0:
            click.echo(pformat(host))
        name = host['name'] or '?'
        for x in ['ip','mac','interface']:
            if host[x] is None:
                host[x] = '?'
        spacer = " " * len("[ {} ]".format(name))
        click.echo("[ {} ] ip {} mac {} interface {}".format(
            click.style(name, bold=True),
            click.style(host['ip'], bold=True),
            click.style(host['mac'], bold=True),
            click.style(host['interface'], bold=True)
            ))
        if not host['state']:
            states = ""
        else:
            states = " ".join(sorted([x.strip() for x in host['state'].split("|")]))
        click.echo("{} state: {}".format(spacer,
            click.style(states, bold=True),
            ))
        if 'templates' in host and len(host['templates'])>0:
            click.echo("{} templates:".format(spacer))
            for k,v in host['templates'].items():
                click.echo("{}     {}: {}".format(spacer, k, v or ''))
        else:
            click.echo("{} templates: -".format(spacer))
        if 'variables' in host and len(host['variables'])>0:
            click.echo("{} variables:".format(spacer))
            for k,v in host['variables'].items():
                click.echo("{}     {}: {}".format(spacer, k, v or ''))
        else:
            click.echo("{} variables: -".format(spacer))
        # build hardware dict
        hardware = {}
        if 'cpu_model' in host:
            hardware['cpu'] = host['cpu_model']
        if 'ram_bytes' in host:
            try:
                hardware['ram'] = humanbytes(int(host['ram_bytes']))
            except:
                pass
        if 'serialnumber' in host:
                hardware['serialnumber'] = host['serialnumber']

        # print hardware stats
        if len(hardware):
            click.echo("{} hardware:".format(spacer))
        for key, value in hardware.items():
            click.echo("{}     {}: {}".format(spacer,key,value))

@cli.command('dnsmasq')
@click.argument('hostname', nargs=-1)
def dnsmasq(hostname):
    """Print dnsmasq configuration"""
    data = host_query(hostname)
    if data is None or len(data)<1:
        raise click.ClickException("No hosts found. Hint: Use % as wildcard.")
    for h in data:
        comment = ''
        # dhcp-host=3c:fd:fe:67:4a:20,node1,10.0.0.1
        if empty_or_None(h['mac']) or empty_or_None(h['name']) or empty_or_None(h['ip']):
            comment = "# "
        click.echo("{}dhcp-host={},{},{}".format(comment, h['mac'] or '?',h['name'] or '?',h['ip'] or '?'))

@cli.command('dhcp')
@click.argument('hostname', nargs=-1)
def dhcp(hostname):
    """Print isc-dhcpd configuration"""
    data = host_query(hostname)
    if data is None or len(data)<1:
        raise click.ClickException("No hosts found. Hint: Use % as wildcard.")
    for h in data:
        h['prefix'] = ''
        if empty_or_None(h['mac']) or empty_or_None(h['name']) or empty_or_None(h['ip']):
            h['prefix'] = "# "
        if empty_or_None(h['name']): h['name'] = '?'
        click.echo("""{prefix}host {name} {{
{prefix}    hardware ethernet {mac};
{prefix}    fixed-address {ip};
{prefix}    option host-name "{name}";
{prefix}}}""".format(**h))


@cli.command('yaml')
@click.argument('hostname', nargs=-1)
def host_yaml(hostname):
    """Print yaml configuration using discovered and configured data"""
    if (len(hostname)<1):
        raise click.ClickException("No hosts found. Hint: Use % as wildcard.")
    data = host_query(hostname)
    if len(data)>0:
        hosts = {}
        for host in data:
            hosts[host['name']] = {
                    'interface':host['interface'],
                    'mac':host['mac'],
                    'ip':host['ip'],
                    }
            if host['class'] is not None:
                hosts[host['name']]['class'] = host['class']

        click.echo(yaml_dump({'hosts':hosts}))

def send_api_command(hostname, command, option=None):
    if (len(hostname)<1):
        raise click.ClickException("No hosts provided. Hint: Use % as wildcard.")
    hosts = host_query(hostname)
    if len(hosts)<1:
        # click.echo("No matching hosts found.")
        raise click.ClickException("No matching hosts found. Hint: Use % as wildcard.")
    for host in hosts:
        if empty_or_None(host['mac']):
            # print warning
            click.echo("No mac address for {} found.".format(host['name']))
            continue
        u = '/api/{}/{}'.format(command,host['mac'])
        if option is not None:
            u += '/' + option
        try:
            reply = query_server(u)
        except requests.exceptions.HTTPError as e:
            raise click.ClickException("{}".format(e))
        except requests.exceptions.ConnectionError:
            raise click.ClickException("Unable to connect to the server.")
        click.echo('[ {} ] {}'.format(
            click.style(host['name'] or host['mac'], bold=True),
            reply))

@cli.command('rediscover')
@click.argument('hostname', nargs=-1)
@click.option('--force', '-f', is_flag=True, help="Force installation.")
def host_rediscover(hostname, force):
    """Ask the host to rediscover"""
    return send_api_command(hostname, 'rediscover', 'force' if force else None)

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
    """Rebuild the host"""
    return send_api_command(hostname, 'rebuild')

@cli.command('update_pxe')
@click.argument('hostname', nargs=-1)
def host_update_pxe(hostname):
    """Rewrite the hosts pxe configuration"""
    return send_api_command(hostname, 'update_pxe')

@cli.command('state')
@click.argument('hostname', nargs=-1)
@click.option('--add')
@click.option('--remove')
def host_state(hostname,add,remove):
    """Add or remove states of a host"""
    msg = ""
    if add:
        msg = send_api_command(hostname, 'add_state', add)
    if remove:
        msg = send_api_command(hostname, 'remove_state', remove)
    return msg

@cli.command('template')
@click.argument('hostname', nargs=1)
@click.argument('template', nargs=1)
def host_template(hostname,template):
    """Fetch the template of a host"""
    txt = query_server("/fetch/{}/{}".format(hostname, template))
    click.echo(txt)

@cli.command('setup')
def serversetup():
    """Setup server configuration"""
    txt = query_server("/api/setup")
    click.echo(txt)

if __name__ == "__main__":
    cli()
