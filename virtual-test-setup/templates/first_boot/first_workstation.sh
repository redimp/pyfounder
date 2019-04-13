#!/bin/bash
echo "Running $0 ..."

# Wait for the Network
NETWORK_WAIT=1
while [ "$NETWORK_WAIT" -ne 0 ]; do
        ping -c 4 {{pyfounder_ip}}
        NETWORK_WAIT=$?
        sleep 5
done

set -e

/usr/bin/wget -q -O /dev/null {{pyfounder_url}}/report/state/{{mac}}/first_boot

/usr/bin/wget -q -O /dev/null {{pyfounder_url}}/report/state/{{mac}}/first_boot_done

echo "Done $0 ."
