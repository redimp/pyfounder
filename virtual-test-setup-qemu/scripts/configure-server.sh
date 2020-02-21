#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

# configure network

SERVER_IP=10.0.70.1

cat << EOF >/etc/network/interfaces.d/default
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp

auto eth1
iface eth1 inet static
    address ${SERVER_IP}
    netmask 255.255.255.0
EOF

# configure dnsmasq (with tftp)

cat << EOF >/etc/dnsmasq.conf
# dont read /etc/hosts
no-hosts
# read hosts from here
addn-hosts=/etc/dnsmasq.hosts
# listen on this address
listen-address=127.0.0.1,${SERVER_IP}
# set the dhcp range
dhcp-range=10.0.70.2,10.0.70.10,1h
# set the ntp server
dhcp-option=option:ntp-server,${SERVER_IP}
# set the gateway
dhcp-option=option:router,${SERVER_IP}
# pxe boot via
dhcp-boot=/pxelinux.0,${SERVER_IP}
# tftp
enable-tftp
tftp-root=/var/lib/tftpboot
EOF

cat << EOF >/etc/dnsmasq.hosts
10.0.70.1	server
10.0.70.2	client0
10.0.70.3	client1
EOF

cat << EOF >/etc/modprobe.d/virtio
9p
9pnet
9pnet_virtio
virtio
EOF


cat << EOF >/etc/default/locale
LC_ALL=C.UTF-8
LANG=C.UTF-8
EOF

# disabled systemd-resolved
systemctl disable systemd-resolved

# disable auto apt
systemctl disable apt-daily.timer

mkdir -p /pyfounder

# create fstab
cat << EOF >/etc/fstab
/dev/sda / ext4 errors=remount-ro,acl 0 1
pyfounder /pyfounder 9p _netdev,trans=virtio,version=9p2000.L 0 0
EOF

mkdir -p /var/lib
ln -s /pyfounder/virtual-test-setup-qemu/tftpboot /var/lib/tftpboot

# run pyfounder provisioning in a screen session

chmod 777 /run/screen

cat <<EOF >/etc/systemd/system/screen-pyfounder.service
[Unit]
Description=Run pyfounder server in screen session
ConditionPathExists=/pyfounder/virtual-test-setup-qemu/scripts/run_pyfounder.sh
RequiresMountsFor=/pyfounder

[Service]
Type=simple
ExecStartPre=/bin/chmod 777 /run/screen
ExecStart=/usr/bin/screen -dmS pyfounder /pyfounder/virtual-test-setup-qemu/scripts/run_pyfounder.sh
ExecStop=/usr/bin/screen -S pyfounder -X quit
TimeoutSec=0
StandardOutput=tty
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl enable screen-pyfounder

# git doesn't like empty last lines
