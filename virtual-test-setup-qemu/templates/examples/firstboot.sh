#!/bin/bash
echo "Running $0 ..."

# Wait for the Network
NETWORK_WAIT=1
while [ "$NETWORK_WAIT" -ne 0 ]; do
        ping -c 4 {{pyfounder_ip}}
        NETWORK_WAIT=$?
        sleep 5
done

{{ pyfounder_update_status("first_boot") }}


{{ pyfounder_update_status("first_boot_done") }}

echo "Done $0 ."
