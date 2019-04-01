#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from pyfounder import db


class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    first_seen = db.Column(db.DateTime())
    last_seen = db.Column(db.DateTime())
    is_installed = db.Column(db.Boolean())

class DiscoveryData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime())
    mac = db.Column(db.String(64))
    cpu_family = db.Column(db.String(64))
    ram_bytes = db.Column(db.Integer)
    vendor_tag = db.Column(db.String(128))
    yaml = db.Column(db.Text)