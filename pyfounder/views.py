#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import re
from pprint import pformat, pprint

from flask import render_template, Response, abort, request

from pyfounder import app, db
from pyfounder.models import HostInfo, HostCommand
from pyfounder import models
from pyfounder.core import Host
from pyfounder import helper
from pyfounder import __version__
from datetime import datetime

@app.route('/')
def index():
    return config()
    #app.logger.warning('sample message')
    return render_template('index.html')

@app.route('/version')
def version():
    content = "pyfounder {}".format(__version__)
    return Response(content, mimetype='text/plain')


@app.route('/config')
def config():
    settings = {}
    # collect all settings
    try:
        settings['PXECFG_DIRECTORY'] = (helper.get_pxecfg_directory(), None)
    except helper.ConfigException as e:
        settings['PXECFG_DIRECTORY'] = (None, "{}".format(e))
    try:
        settings['PYFOUNDER_HOSTS'] = (helper.get_hosts_yaml(), None)
    except helper.ConfigException as e:
        settings['PYFOUNDER_HOSTS'] = (None, "{}".format(e))
    try:
        settings['PYFOUNDER_TEMPLATES'] = (
            helper.get_template_directory(), None)
    except helper.ConfigException as e:
        settings['PYFOUNDER_TEMPLATES'] = (None, "{}".format(e))

    try:
        extra = pformat(helper.load_hosts_config())
    except helper.ConfigException as e:
        extra = "Error: {}".format(e)
    # add settings to the config_arr
    return render_template('config.html', settings=settings, extra=extra)


def fetch_template(template_name, hostname):
    cfg = helper.host_config(hostname)
    # find template filename
    try:
        template_file = cfg['templates'][template_name]
    except KeyError as e:
        print(e)
        abort(404, "Template {} not configured for host {}.".format(
            template_name, hostname))
    try:
        rendered_content = helper.configured_template(template_file,cfg)
    except Exception as e:
        abort(404, "Template {} file not found for host {}\n{}.".format(
            template_name, hostname, e))
    return rendered_content


@app.route('/fetch/<string:hostname>')
@app.route('/fetch/<string:hostname>/')
@app.route('/fetch/<string:hostname>/<string:template_name>')
def fetch(hostname, template_name=None):
    try:
        cfg = helper.host_config(hostname)
    except ValueError as e:
        abort(404, "Host {} not found.".format(hostname))
    if template_name is None:
        ymlcfg = helper.yaml_dump(cfg)
        return Response(ymlcfg, mimetype='text/plain')
    rendered_content =  fetch_template(template_name, hostname)
    return Response(rendered_content, mimetype='text/plain')

@app.route('/discovery-report/', methods=['POST','GET'])
@app.route('/discovery-report', methods=['POST','GET'])
def discovery_report():
    _data = request.form.get('data')
    _error = request.form.get('error')
    if _data is not None:
        try:
           data = helper.yaml_load(_data)
        except:
            print(_data)
            raise
        # store data
        #print(data)
        host = HostInfo.query.filter_by(mac=data['mac']).first()
        if host is None:
            app.logger.info('New Discovered Host: {}'.format(data['mac']))
            # create host
            host = models.HostInfo(mac=data['mac'], first_seen=datetime.utcnow())
        else:
            app.logger.info('Updated Discovered Host: {}'.format(data['mac']))
        # update host data
        host.last_seen = datetime.utcnow()
        host.serialnumber = data['serialnumber']
        host.cpu_model = data['cpu_model']
        host.ram_bytes = data['ram_bytes']
        host.interface = data['interface']
        host.discovery_yaml = _data
        host.remove_state('rediscover')
        host.add_state('discovered')
        # store in database
        db.session.add(host)
        db.session.commit()
        host = models.HostInfo.query.filter_by(mac=data['mac']).first()
        return str(host.mac)
    if _error is not None:
        app.logger.warning('Discovery Error: {}'.format(_error))
        # TODO add to database
        pass
    return ''

@app.route('/discovery-remote-control/<mac>')
def discovery_remote_control(mac):
    # check host
    host = models.HostInfo.query.filter_by(mac=mac).first()
    if host is None:
        # log
        app.logger.warning('Unknown host asking for command {} '.format(mac))
        abort(404)
    # update last_seen
    host.last_seen = datetime.utcnow()
    # check for any
    command = models.HostCommand.query.filter_by(mac=mac,received=None).first()
    if command is None:
        db.session.add(host)
        db.session.commit()
        return 'wait'
    # set or remove states
    if command.add_state is not None:
        host.add_state(command.add_state)
    if command.remove_state is not None:
        host.remove_state(command.remove_state)
    # host into database
    db.session.add(host)
    # update command
    command.received = datetime.utcnow()
    db.session.add(command)
    db.session.commit()
    app.logger.info('Host {} received command {} '.format(mac, command.command))
    return command.command

@app.route('/fetch-discovery')
def fetch_discovery():
    # TODO log
    try:
        with open(app.config['PYFOUNDER_DISCOVERY_SCRIPT']) as f:
            content = f.read()
    except:
        abort(500)
    return Response(content, mimetype='text/plain')

@app.route('/api/hosts')
@app.route('/api/hosts/')
@app.route('/api/hosts/<pattern>')
def api_hosts(pattern=None):
    # build the query
    query = HostInfo.query
    if pattern is not None:
        # extend the query
        query = query.filter(
                    HostInfo.name.ilike('{}'.format(pattern)) |
                    HostInfo.mac.ilike('{}'.format(pattern))
                )
    hosts_config = helper.load_hosts_config()
    host_data = []
    for q in query.all():
        h = Host(_model=q)
        # update from host_config
        if h['name'] is not None and h['name'] in hosts_config:
            h.from_dict(hosts_config[h['name']])
        elif h['mac'] is not None:
            n = helper.find_hostname_by_mac(h['mac'],hosts_config)
            if n is not None:
                h.from_dict(hosts_config[n])
        host_data.append(h)
    hostnames_query = [x['name'] for x in host_data if 'name' in x.data]
    # complete data with hosts_data
    for missing_host in [x for x in hosts_config.keys() if x not in hostnames_query]:
        missing_mac = hosts_config[missing_host]['mac']
        if pattern is not None:
            pattern_re = re.escape(pattern)
            pattern_re = pattern_re.replace('\\%','.*')
            pattern_re = "^{}$".format(pattern_re)
            if not re.match(pattern_re, missing_host) and not re.match(pattern_re, missing_mac):
                continue
        host_data.append(Host(_dict=hosts_config[missing_host]))
    yaml_str = helper.yaml_dump([h.data for h in host_data])
    return Response(yaml_str, mimetype='text/plain')


def get_host(mac):
    hosts_config = helper.load_hosts_config()
    host_config = None
    n = helper.find_hostname_by_mac(mac,hosts_config)
    if n is not None:
        host_config = hosts_config[n]
    query = HostInfo.query.filter_by(mac=mac).first()
    host = Host(_model = query, _dict=host_config)
    return host

@app.route('/report/state/<mac>/<state>')
def report_state(mac, state):
    # find host
    host = get_host(mac)
    hi = host.get_hostinfo()
    app.logger.info(
        'Host {} reports state: {}'.format(host.data['name'], state)
        )
    if state == "early_command":
        hi.remove_state("reboot_in_preseed")
        hi.add_state("early_command")
    if state == "early_command_done":
        hi.remove_state("early_command","reboot_in_preseed")
        hi.add_state("early_command_done")
    elif state == "late_command":
        hi.remove_state("early_command","early_command_done","reboot_in_preseed")
        hi.add_state("late_command")
    elif state == "late_command_done":
        hi.remove_state("late_command")
        hi.add_state("reboot_out_preseed")
        # update pxelinux.cfg
        pxe_config = fetch_template('pxelinux.cfg', host.data['name'])
        host.update_pxelinux_cfg(pxe_config)
    elif state == "first_boot":
        hi.remove_state("reboot_out_preseed")
        hi.add_state("first_boot")
    elif state == "first_boot_done":
        hi.remove_state("first_boot")
        hi.add_state("installed")
    else:
        hi.add_state(state)
    db.session.add(hi)
    db.session.commit()
    return "ok"

@app.route('/api/rediscover/<mac>')
def api_rediscover(mac):
    # find host
    host = get_host(mac)
    # TODO check if host is already installed
    # delete pxelinux.cfg/<mac>
    host.remove_pxelinux_cfg()
    # delete from database
    h = host.get_hostinfo()
    if h is None:
        h = HostInfo()
        h.mac = mac
    else:
        h.serialnumber = None
        h.cpu_model = None
        h.ram_bytes = None
        h.gpu = None
        h.discovery_yaml = None
    # send rediscover command
    h.remove_state('discovered')
    host.send_command('discover')
    return "ok."

@app.route('/api/rebuild/<mac>')
def api_rebuild(mac):
    # find host
    # write install pxelinux.cfg/<mac>
    # "send:" reboot command
    return "WIP"

@app.route('/api/remove/<mac>')
def api_remove(mac):
    # find host
    host = get_host(mac)
    hi = host.get_hostinfo()
    app.logger.warning('Removing {} {}.'.format(host['name'] or '?',mac))
    # remove pxelinux.cfg/<mac>
    host.remove_pxelinux_cfg()
    # remove Host from database
    HostCommand.query.filter_by(mac=mac).delete()
    HostInfo.query.filter_by(mac=mac).delete()
    db.session.commit()
    # "send:" reboot command
    return "ok."

@app.route('/api/install/<mac>')
@app.route('/api/install/<mac>/<option>')
def api_install(mac,option=None):
    # find host
    host = get_host(mac)
    # TODO check if host is already installed
    hi = host.get_hostinfo()
    pprint(hi.has_state('installed'))
    if hi is not None and hi.has_state('installed') and (option is None or "force" not in option):
        return "Error: Host is already installed. Please use --force if you want to reinstall."
    if hi is None or not hi.has_state('discovered'):
        return "Error: Host is not discovered yet."
    # check host infos
    if helper.empty_or_None(host.data['name']):
        return "Error: No name configured yet."
    # write install pxelinux.cfg/<mac>
    pxe_config = fetch_template('pxelinux.cfg-install', host.data['name'])
    host.update_pxelinux_cfg(pxe_config)
    host.send_command('reboot', add_state='reboot_in_preseed')
    hi.remove_state("installed")
    db.session.add(hi)
    db.session.commit()
    return "send command to reboot into preseed."


