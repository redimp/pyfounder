#!/bin/bash

set -e

TARGET_DIR=$PWD/tftpboot
RELEASE=bionic

test -d $TARGET_DIR/pxelinux.cfg || { echo "Error: Missing $TARGET_DIR/pxelinux.cfg."; exit 1; }

for F in vmlinuz initrd filesystem.squashfs; do
	if ! test -f $TARGET_DIR/pyfounder-discovery/$F; then
		mkdir -p $TARGET_DIR/pyfounder-discovery
		test -f ../netboot-discovery/image/$F || \
			{ echo "Error: ../netboot-discovery/image/$F not found."; exit 1; }
		cp ../netboot-discovery/image/$F $TARGET_DIR/pyfounder-discovery/$F
	fi
done

NETBOOT_TAR_GZ_URL=http://archive.ubuntu.com/ubuntu/dists/${RELEASE}-updates/main/installer-amd64/current/images/netboot/netboot.tar.gz

NETBOOT_TAR_GZ=download/${RELEASE}-netboot.tar.gz

if [ ! -f $NETBOOT_TAR_GZ ]; then
	wget -O $NETBOOT_TAR_GZ $NETBOOT_TAR_GZ_URL
fi

mkdir -p $TARGET_DIR/${RELEASE}

if [ ! -f $TARGET_DIR/${RELEASE}/ubuntu-installer/amd64/pxelinux.0 ]; then
	tar --directory $TARGET_DIR/${RELEASE} -xf $NETBOOT_TAR_GZ
fi

if [ ! -e $TARGET_DIR/pxelinux.0 ]; then
	(
	cd $TARGET_DIR
	ln -s ${RELEASE}/ubuntu-installer/amd64/pxelinux.0
	)
fi

if [ ! -e $TARGET_DIR/ldlinux.c32 ]; then
	(
	cd $TARGET_DIR
	ln -s ${RELEASE}/ldlinux.c32
	)
fi

# if [ ! -f $TARGET_DIR/pxelinux.cfg/ ]; then
# # default file
# cat << EOF >$TARGET_DIR/pxelinux.cfg/installer
# default install
# timeout 0
# LABEL install
#         kernel ${RELEASE}/ubuntu-installer/amd64/linux
#         append vga=normal initrd=${RELEASE}/ubuntu-installer/amd64/initrd.gz locale=en_US.UTF-8 debian-installer/keymap=us pkgsel/install-language-support=false netcfg/dhcp_timeout=120 console-setup/layoutcode=us console-setup/ask_detect=false
# EOF
# 
# fi
