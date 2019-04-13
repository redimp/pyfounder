#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:
import os

DEBUG = False  # make sure DEBUG is off unless enabled explicitly otherwise
LOG_DIR = '.'  # create log files in current working directory
SQLALCHEMY_DATABASE_URI = 'sqlite://'
SQLALCHEMY_TRACK_MODIFICATIONS = False
PXECFG_DIRECTORY = ''
PYFOUNDER_HOSTS = ''
PYFOUNDER_IP = ''
PYFOUNDER_URL = ''
PYFOUNDER_TEMPLATES = ''
PYFOUNDER_DISCOVERY_SCRIPT = os.path.join(os.path.abspath(os.path.dirname(__file__)),'pyfounder-discovery-tool.py')
