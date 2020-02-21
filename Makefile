ROOT_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

all: run

clean:
	rm -rf venv && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	virtualenv --python=python3 venv
	venv/bin/pip install -e $(ROOT_DIR)

debug: venv
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=pyfounder.server PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run

run: venv
	FLASK_APP=pyfounder.server PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run --host 0.0.0.0

test: venv
	venv/bin/python -m unittest discover -s tests

venv/bin/founder-complete.bash: venv pyfounder/cli.py
	_FOUNDER_COMPLETE=source venv/bin/founder >venv/bin/founder-complete.bash; true
