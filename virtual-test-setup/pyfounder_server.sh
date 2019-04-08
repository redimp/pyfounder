#!/bin/bash

PYFOUNDER_DIRECTORY="/usr/local/lib/pyfounder"
VENVBIN=$PYFOUNDER_DIRECTORY/venv/bin
PYTHON=$VENVBIN/python
PIP=$VENVBIN/pip

test -d $PYFOUNDER_DIRECTORY || mkdir -p $PYFOUNDER_DIRECTORY

cd $PYFOUNDER_DIRECTORY

test -d venv || python3 -m virtualenv -p python3 venv

# wait for /vagrant to come up
while true; do
  test -f /vagrant/Vagrantfile && break
  sleep 5
done

cd /pyfounder
$PIP install -U -r requirements.txt
#$PYTHON setup.py develop
$PIP install -e .

export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_APP=pyfounder
export PYFOUNDER_SETTINGS=/vagrant/server-settings.cfg
# run flask
$VENVBIN/flask run --host=0.0.0.0
