all: run

clean:
	rm -rf venv && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	virtualenv --python=python3 venv
#	venv/bin/pip install -r requirements.txt
	venv/bin/python setup.py develop

debug: venv
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=pyfounder PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run

run: venv
	FLASK_APP=pyfounder PYFOUNDER_SETTINGS=../settings.cfg venv/bin/flask run

test: venv
	PYFOUNDER_SETTINGS=../settings.cfg venv/bin/python -m unittest discover -s tests

sdist: venv test
	venv/bin/python setup.py sdist
