#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

from flask_sqlalchemy import SQLAlchemy
from pyfounder import app
db = SQLAlchemy(app)

class HostInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    first_seen = db.Column(db.DateTime())
    last_seen = db.Column(db.DateTime())
    state = db.Column(db.String(255))
    mac = db.Column(db.String(64))
    serialnumber = db.Column(db.String(128))
    cpu_model = db.Column(db.String(64))
    ram_bytes = db.Column(db.Integer)
    gpu = db.Column(db.String(128))
    discovery_yaml = db.Column(db.Text)

    def __repr__(self):
        return "<Host {} {} {}>".format(self.id, self.name or '?', self.mac or '?')


    def get_states(self):
        if self.state is None:
            return []
        return self.state.split('|')

    def has_state(self, state):
        states = self.get_states()
        return state in states

    def add_state(self, state, *more_states):
        states = self.get_states()
        states.append(state)
        if len(more_states):
            states += more_states
        self.state = "|".join(states)

    def remove_state(self, state, *more_states):
        states = self.get_states()
        for s in [state] + list(more_states):
            try:
                states.remove(s)
            except ValueError:
                pass
        self.state = "|".join(states)

db.create_all()

