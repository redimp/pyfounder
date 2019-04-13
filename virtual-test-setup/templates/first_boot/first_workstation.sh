#!/bin/sh
wget -q -O /dev/null http://{{pyfounder_ip}}:5000/report/state/{{mac}}/first_boot

wget -q -O /dev/null http://{{pyfounder_ip}}:5000/report/state/{{mac}}/first_boot_done
