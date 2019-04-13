#!/bin/sh
wget -q -O /dev/null http://{{pyfounder_ip}}:5000/report/state/{{mac}}/late_command

# download first_boot script
mkdir -p /target/root/phpseed
wget {{pyfounder_url}}/fetch/{{name}}/first_boot.sh -O /target/root/phpseed/first_boot.sh
chmod +x /target/root/phpseed/first_boot.sh
# activate first_boot script
echo "@reboot root /target/root/phpseed/first_boot.sh && rm /etc/cron.d/pyfounder_first_boot" >> /etc/cron.d/pyfounder_first_boot

wget -q -O /dev/null http://{{pyfounder_ip}}:5000/report/state/{{mac}}/late_command_done
