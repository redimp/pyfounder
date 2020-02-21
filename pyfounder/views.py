#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import re
from pprint import pformat, pprint

from flask import render_template, Response, abort, request

from pyfounder.server import app, db
from pyfounder.models import HostInfo, HostCommand
from pyfounder import models
import pyfounder.core
from pyfounder.core import Host, get_host
from pyfounder import helper
from pyfounder.helper import fetch_template, ConfigException
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


@app.route('/fetch/<string:hostname>')
@app.route('/fetch/<string:hostname>/')
@app.route('/fetch/<string:hostname>/<string:template_name>')
def fetch(hostname, template_name=None):
    try:
        cfg = helper.host_config(hostname)
    except ConfigException as e:
        abort(404, "Host {} not found.".format(hostname))
    if template_name is None:
        ymlcfg = helper.yaml_dump(cfg)
        return Response(ymlcfg, mimetype='text/plain')
    try:
        rendered_content = fetch_template(template_name, hostname)
    except ConfigException as e:
        abort(404, "{}".format(e))
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
        host_info = HostInfo.query.filter_by(mac=data['mac'].lower()).first()
        if host_info is None:
            app.logger.info('New Discovered Host: {}'.format(data['mac']))
            # create host_info
            host_info = models.HostInfo(mac=data['mac'].lower(), first_seen=datetime.utcnow())
        else:
            app.logger.info('Updated Discovered Host: {}'.format(data['mac']))
        # update host data
        host_info.last_seen = datetime.utcnow()
        host_info.serialnumber = data['serialnumber']
        host_info.cpu_model = data['cpu_model']
        host_info.ram_bytes = data['ram_bytes']
        host_info.interface = data['interface']
        host_info.discovery_yaml = _data
        host_info.remove_state('rediscover')
        host_info.add_state('discovered')
        # store in database
        db.session.add(host_info)
        db.session.commit()
        host_info = models.HostInfo.query.filter_by(mac=data['mac'].lower()).first()
        return str(host_info.mac)
    if _error is not None:
        app.logger.warning('Discovery Error: {}'.format(_error))
        # TODO add to database
        pass
    return ''

@app.route('/discovery-remote-control/<mac>')
def discovery_remote_control(mac):
    # check host
    host = get_host(mac=mac)
    if host is None:
        # log
        app.logger.warning('Unknown host asking for command {} '.format(mac))
        abort(404, "Host not found.")
    host_info = host.get_hostinfo()
    # host_info = models.HostInfo.query.filter_by(mac=mac).first()
    # update last_seen
    host_info.last_seen = datetime.utcnow()
    # check for any
    command = models.HostCommand.query.filter_by(mac=mac,received=None).first()
    if command is None:
        db.session.add(host_info)
        db.session.commit()
        return 'wait'
    # set or remove states
    if command.add_state is not None:
        host_info.add_state(command.add_state)
    if command.remove_state is not None:
        host_info.remove_state(command.remove_state)
    # update hostinfo in database
    db.session.add(host_info)
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
        try:
            missing_mac = hosts_config[missing_host]['mac']
        except KeyError:
            missing_mac = None
        if pattern is not None and missing_mac is not None:
            pattern_re = re.escape(pattern)
            pattern_re = pattern_re.replace('\\%','.*')
            pattern_re = "^{}$".format(pattern_re)
            if not re.match(pattern_re, missing_host) and not re.match(pattern_re, missing_mac):
                continue
        host_data.append(Host(_dict=hosts_config[missing_host]))
    yaml_str = helper.yaml_dump([h.data for h in host_data])
    return Response(yaml_str, mimetype='text/plain')

@app.route('/report/state/<mac>/<state>')
def report_state(mac, state):
    # find host
    host = get_host(mac)
    hi = host.get_hostinfo()
    app.logger.info(
        'Host {} reports state: {}'.format(host.data['name'], state)
        )
    try:
        host.enter_state(state)
    except Exception as e:
        # log error
        app.logger.warning('Error: {}'.format(e))
        abort(500,"Error: {}".format(e))

    return "ok"

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
        try:
            # update pxelinux.cfg
            host.update_pxelinux_cfg('default')
        except Exception as e:
            # log error
            app.logger.warning('Error: {}'.format(e))
            abort(500,"Error: {}".format(e))
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
@app.route('/api/rediscover/<mac>/<option>')
def api_rediscover(mac, option=None):
    # find host
    host = get_host(mac)
    # check if host is already installed
    host_info = host.get_hostinfo()
    if host_info is not None and host_info.has_state('installed') and \
            (option is None or "force" not in option):
        return "Error: Host is already installed. Please use --force if you want to rediscover the host."

    # delete old infos from database
    if host_info is None:
        host_info = HostInfo()
        host_info.mac = mac
    else:
        host_info.serialnumber = None
        host_info.cpu_model = None
        host_info.ram_bytes = None
        host_info.gpu = None
        host_info.discovery_yaml = None
    # remove all states
    host_info.state = ""
    db.session.add(host_info)
    db.session.commit()
    # update pxelinux.cfg
    host.update_boot_cfg()
    host.send_command('discover')
    # send rediscover command
    return "ok."

@app.route('/api/add_state/<mac>/<states>')
def api_add_state(mac,states):
    # find host
    host = get_host(mac)
    hi = host.get_hostinfo()
    state_list = re.findall(r'([a-zA-Z\-_0-9]+)',states)
    if (len(state_list)<1):
        abort(400,"Missing state")
    hi.add_state(*state_list)
    # update database
    db.session.add(hi)
    db.session.commit()
    # update boot cfg
    host.update_boot_cfg()
    return "Host {} states: {}".format(mac, " ".join(hi.get_states()))

@app.route('/api/remove_state/<mac>/<states>')
def api_remove_state(mac,states):
    # find host
    host = get_host(mac)
    hi = host.get_hostinfo()
    state_list = re.findall(r'([a-zA-Z\-_0-9]+)',states)
    if (len(state_list)<1):
        abort(400,"Missing state")
    hi.remove_state(*state_list)
    # update database
    db.session.add(hi)
    db.session.commit()
    # update boot cfg
    host.update_boot_cfg()
    return "Host {} states: {}".format(mac, " ".join(hi.get_states()))

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
    hi = host.get_hostinfo()
    # check if host is already installed
    if hi is not None and hi.has_state('installed') and (option is None or "force" not in option):
        return "Error: Host is already installed. Please use --force if you want to reinstall."
    if hi is None or not hi.has_state('discovered'):
        return "Error: Host is not discovered yet."
    # check host infos
    if helper.empty_or_None(host.data['name']):
        return "Error: No name configured yet."
    # write install pxelinux.cfg/<mac>
    #host.update_pxelinux_cfg("install")
    host.enter_state("reboot_into_preseed")
    host.send_command('reboot', add_state='booting_into_preseed')
    #hi.remove_state("installed")
    db.session.add(hi)
    db.session.commit()
    return "send command to reboot into preseed."


@app.route('/api/setup')
def api_setup():
    messages = []
    content = helper.fetch_template_pxe_discovery()
    filename = os.path.join(helper.get_pxecfg_directory(), "default")
    with open(filename, "w") as f:
        f.write(content)
    print(content)
    messages.append("file: {} updated.".format(filename))
    return "\n".join(messages)
