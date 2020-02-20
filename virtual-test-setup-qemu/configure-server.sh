#!/bin/bash

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

cat /etc/dnsmasq.conf

# disabled systemd-resolved
systemctl disable systemd-resolved

# disable auto apt
systemctl disable apt-daily.timer


