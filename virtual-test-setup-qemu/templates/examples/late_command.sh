#!/bin/sh
{{ pyfounder_update_status("late_command") }}

# install some core packages
DEBIAN_FRONTEND=noninteractive apt-install --install-recommends vim ssh python

# download first_boot script
mkdir -p /target/root/pyfounder
mkdir -p /target/var/log/pyfounder
wget {{pyfounder_url}}/fetch/{{name}}/first_boot.sh -O /target/root/pyfounder/first_boot.sh
chmod +x /target/root/pyfounder/first_boot.sh
# activate first_boot script
echo "@reboot root bash /root/pyfounder/first_boot.sh pyfounder 2>&1 | /usr/bin/logger -t pyfounder && mv /etc/cron.d/pyfounder_first_boot /root/pyfounder" > /target/etc/cron.d/pyfounder_first_boot

{{ pyfounder_update_status("late_command_done") }}
