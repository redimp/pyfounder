import os
from flask import Flask
import flask.helpers

app = Flask(__name__)
app.config.from_object('pyfounder.default_settings')
if 'PYFOUNDER_SETTINGS' in os.environ:
    app.config.from_envvar('PYFOUNDER_SETTINGS')

if not flask.helpers.get_debug_flag():
    import logging
    from logging.handlers import TimedRotatingFileHandler
    # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
    file_handler = TimedRotatingFileHandler(os.path.join(app.config['LOG_DIR'], 'pyfounder.log'), 'midnight')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
    app.logger.addHandler(file_handler)

import pyfounder.views
