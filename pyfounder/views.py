#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from flask import render_template

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

    # add settings to the config_arr
    return render_template('config.html', settings=settings)

