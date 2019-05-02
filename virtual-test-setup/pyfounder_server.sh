#!/bin/bash

### Firewall / Router

modprobe ip_tables
modprobe ip_conntrack
modprobe iptable_nat

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -F

OUTER_IF=enp0s3
INNER_IF=enp0s8

iptables -A FORWARD -o $OUTER_IF -i $INNER_IF -s 10.0.10.0/24 -m conntrack --ctstate NEW -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -t nat -A POSTROUTING -o $OUTER_IF -j MASQUERADE


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

systemctl restart dnsmasq

cd /pyfounder
$PIP install -U -r requirements.txt
#$PYTHON setup.py develop
$PIP install -e .

export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_APP=pyfounder.server
export PYFOUNDER_SETTINGS=/vagrant/server-settings.cfg
# run flask
$VENVBIN/flask run --host=0.0.0.0

