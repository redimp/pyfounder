#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from pprint import pformat, pprint

from flask import render_template, Response, abort, request

from pyfounder import app
from pyfounder.models import db, HostInfo
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


@app.route('/fetch/<string:hostname>')
@app.route('/fetch/<string:hostname>/')
@app.route('/fetch/<string:hostname>/<string:template_name>')
def fetch(hostname, template_name=None):
    try:
        cfg = helper.host_config(hostname)
    except ValueError as e:
        abort(404, "Host {} not found.".format(hostname))
    if template_name is None:
        ymlcfg = yaml_dump(cfg)
        return Response(ymlcfg, mimetype='text/plain')
    # find template filename
    try:
        template_file = cfg['templates'][template_name]
    except KeyError as e:
        abort(404, "Template {} not configured for host {}.".format(
            template_name, hostname))
    rendered_content = helper.configured_template(template_file,
                                                  cfg)
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
        host.discovery_yaml = _data
        host.add_state('discovered','not_installed')
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
    # TODO check status and update status
    host = models.HostInfo.query.filter_by(mac=mac).first()
    if host is None or not host.has_state('discovered'):
        # no discovery data found, ask client to discover
        return 'discover'
    # check if host is configured
    hostname = helper.find_hostname_by_mac(mac)
    if hostname is None:
        return 'wait'
    config = helper.host_config(hostname)
    host.name = config['hostname']
    host.last_seen = datetime.utcnow()
    host.add_state('boot_into_install')
    db.session.add(host)
    db.session.commit()
    app.logger.info('Reboot Host {} {} into install.'.format(host.name, host.mac))

    return 'reboot'

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

    #import pdb; pdb.set_trace()
    hostnames_query = [x['name'] for x in host_data if 'name' in x.data]
    # complete data with hosts_data
    for missing_host in [x for x in hosts_config.keys() if x not in hostnames_query]:
        host_data.append(Host(_dict=hosts_config[missing_host]))
    yaml_str = helper.yaml_dump([h.data for h in host_data])
    return Response(yaml_str, mimetype='text/plain')

@app.route('/api/rediscover/<hostname>')
def api_rediscover(hostname):
    # find host
    # delete pxelinux.cfg/<mac>
    # ? delete from database
    # "send:" reboot command
    return "WIP"

@app.route('/api/rebuild/<hostname>')
def api_rebuild(hostname):
    # find host
    # write install pxelinux.cfg/<mac>
    # "send:" reboot command
    return "WIP"

@app.route('/api/install/<hostname>')
def api_install(hostname):
    # find host
    # write install pxelinux.cfg/<mac>
    # "send:" reboot command
    return "WIP"
