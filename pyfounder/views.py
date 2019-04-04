#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from pprint import pformat

from flask import render_template, Response, abort, request

from pyfounder import app
from pyfounder.models import db
from pyfounder import models
from pyfounder import helper
from pyfounder import __version__
from datetime import datetime

from yaml import load, dump, add_representer
try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

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
        from yaml import dump
        ymlcfg = dump(cfg)
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
    data = load(_data, Loader=Loader)
    # TODO store data
    print(data['mac'])
    host = models.DiscoveredHost.query.filter_by(mac=data['mac']).first()
    print(host)
    if host is not None:
        # TODO log
        pass
    else:
        # create host
        host = models.DiscoveredHost(mac=data['mac'], date=datetime.utcnow(), yaml=_data)
        db.session.add(host)
        db.session.commit()

    # TODO return id
    return '42'

@app.route('/discovery-remote-control/<id>')
def discovery_remote_control(id):
    # TODO check status and update status
    return 'quit'

@app.route('/fetch-discovery')
def fetch_discovery():
    # TODO log
    try:
        with open(app.config['PYFOUNDER_DISCOVERY_SCRIPT']) as f:
            content = f.read()
    except:
        abort(500)
    return Response(content, mimetype='text/plain')
