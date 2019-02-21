#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from pprint import pformat

from flask import render_template, Response, abort

from pyfounder import app
from pyfounder import helper

@app.route('/')
def index():
    return config()
    #app.logger.warning('sample message')
    return render_template('index.html')

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
        settings['PYFOUNDER_TEMPLATES'] = (helper.get_template_directory(), None)
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
def fetch(hostname,template_name=None):
    try:
        cfg = helper.host_config(hostname)
    except ValueError as e:
        abort(404, "Hostname {} not found.".format(hostname))
    if template_name is None:
        from yaml import dump
        ymlcfg = dump(cfg)
        return Response(ymlcfg, mimetype='text/plain')
    # find template filename
    try:
        template_file= cfg['templates'][template_name]
    except KeyError as e:
        abort(404, "Template {} not configured for host {}.".format(
            template_name,hostname))
    # load the jinja stuff
    from jinja2 import FileSystemLoader, Environment
    from jinja2.exceptions import TemplateNotFound
    # create context
    context = cfg
    for key, value in cfg['variables'].items():
        context[key] = value
    # FIXME: should env be global?
    env = Environment(
            loader=FileSystemLoader(helper.get_template_directory()))
    try:
        # load template
        template = env.get_template(template_file)
    except TemplateNotFound as e:
        abort(404, "Template {} not found.".format(template_file))
    # render
    rendered_content = template.render(**context)
    return Response(rendered_content, mimetype='text/plain')
    abort(400)
