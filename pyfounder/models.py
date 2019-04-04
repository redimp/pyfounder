#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from flask_sqlalchemy import SQLAlchemy
from pyfounder import app
db = SQLAlchemy(app)

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    first_seen = db.Column(db.DateTime())
    last_seen = db.Column(db.DateTime())
    is_installed = db.Column(db.Boolean())

class DiscoveredHost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime())
    mac = db.Column(db.String(64))
    cpu_family = db.Column(db.String(64))
    ram_bytes = db.Column(db.Integer)
    serialnumber = db.Column(db.String(128))
    yaml = db.Column(db.Text)

db.create_all()

