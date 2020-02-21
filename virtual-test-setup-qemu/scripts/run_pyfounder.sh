#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

### Firewall / Router

modprobe ip_tables
modprobe ip_conntrack
modprobe iptable_nat

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -F

OUTER_IF=eth0
INNER_IF=eth1
INNER_NET=10.0.70.0/24

iptables -A FORWARD -o $OUTER_IF -i $INNER_IF -s $INNER_NET -m conntrack --ctstate NEW -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -t nat -A POSTROUTING -o $OUTER_IF -j MASQUERADE


export LC_ALL=C.UTF-8
export LANG=C.UTF-8

PIP=$(which pip3)

cd /pyfounder
$PIP install -U -r requirements.txt
$PIP install -e .

# configure founder for root user
founder client --url http://10.0.70.1:5000/

# configure server environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_APP=pyfounder.server
export PYFOUNDER_SETTINGS=/pyfounder/virtual-test-setup-qemu/server-settings.cfg
# run server via flask
flask run --host=0.0.0.0

