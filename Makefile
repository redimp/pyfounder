ROOT_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

all: run

clean:
	rm -rf venv && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	virtualenv --python=python3 venv
#	venv/bin/pip install -r requirements.txt
#	venv/bin/python setup.py develop
	venv/bin/pip install -e $(ROOT_DIR)

venv-vagrant:
	virtualenv --python=python3 venv-vagrant
#	venv-vagrant/bin/pip install -r requirements.txt
	venv-vagrant/bin/python setup.py develop

debug: venv
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=pyfounder.server PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run

run: venv
	FLASK_APP=pyfounder.server PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run --host 0.0.0.0

vagrant-server: venv-vagrant
	FLASK_APP=pyfounder.server PYFOUNDER_SETTINGS=../settings.vagrant-server.cfg venv-vagrant/bin/flask run --host 0.0.0.0

test: venv
	venv/bin/python -m unittest discover -s tests

sdist: venv test
	venv/bin/python setup.py sdist

venv/bin/founder-complete.bash: venv pyfounder/cli.py
	_FOUNDER_COMPLETE=source venv/bin/founder >venv/bin/founder-complete.bash; true
