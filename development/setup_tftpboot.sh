#!/bin/bash

set -e

TARGET_DIR=$PWD/tftpboot
RELEASE=bionic

mkdir -p $TARGET_DIR/pxelinux.cfg

NETBOOT_TAR_GZ_URL=http://archive.ubuntu.com/ubuntu/dists/${RELEASE}-updates/main/installer-amd64/current/images/netboot/netboot.tar.gz

NETBOOT_TAR_GZ=${RELEASE}-netboot.tar.gz

if [ ! -f $NETBOOT_TAR_GZ ]; then
	wget -O ${RELEASE}-netboot.tar.gz $NETBOOT_TAR_GZ_URL
fi

mkdir -p $TARGET_DIR/${RELEASE}

if [ ! -f $TARGET_DIR/${RELEASE}/ubuntu-installer/amd64/pxelinux.0 ]; then
	tar --directory $TARGET_DIR/${RELEASE} -xf $NETBOOT_TAR_GZ
fi

if [ ! -e $TARGET_DIR/pxelinux.0 ]; then
	ln -s $TARGET_DIR/${RELEASE}/ubuntu-installer/amd64/pxelinux.0 $TARGET_DIR/pxelinux.0
fi

if [ ! -f $TARGET_DIR/pxelinux.cfg/default ]; then
# default file
cat << EOF >$TARGET_DIR/pxelinux.cfg/default
default install
timeout 0
LABEL install
        kernel ${RELEASE}/ubuntu-installer/amd64/linux
        append vga=normal initrd=${RELEASE}/ubuntu-installer/amd64/initrd.gz locale=en_US.UTF-8 debian-installer/keymap=us
EOF

fi
