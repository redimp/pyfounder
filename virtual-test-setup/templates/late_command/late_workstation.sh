#!/bin/sh
wget -q -O /dev/null {{pyfounder_url}}/report/state/{{mac}}/late_command

# install some core packages
DEBIAN_FRONTEND=noninteractive apt-install --install-recommends vim ssh python

# download first_boot script
mkdir -p /target/root/pyfounder
mkdir -p /target/var/log/pyfounder
wget {{pyfounder_url}}/fetch/{{name}}/first_boot.sh -O /target/root/pyfounder/first_boot.sh
chmod +x /target/root/pyfounder/first_boot.sh
# activate first_boot script
echo "@reboot root bash /root/pyfounder/first_boot.sh pyfounder 2>&1 | /usr/bin/logger -t pyfounder && rm -f /etc/cron.d/pyfounder_first_boot" > /target/etc/cron.d/pyfounder_first_boot

wget -q -O /dev/null {{pyfounder_url}}/report/state/{{mac}}/late_command_done
