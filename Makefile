ROOT_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

all: run

clean:
	rm -rf venv && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	virtualenv --python=python3 venv
#	venv/bin/pip install -r requirements.txt
#	venv/bin/python setup.py develop
	venv/bin/pip install -e $(ROOT_DIR)

debug: venv
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=pyfounder PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run

run: venv
	FLASK_APP=pyfounder PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run

test: venv
	venv/bin/python -m unittest discover -s tests

sdist: venv test
	venv/bin/python setup.py sdist

venv/bin/founder-complete.bash: venv pyfounder/cli.py
	_FOUNDER_COMPLETE=source venv/bin/founder >venv/bin/founder-complete.bash; true
