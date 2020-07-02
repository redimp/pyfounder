#!/bin/bash

set -e

[ "$WORK_DIR" == "" ] && WORK_DIR=$PWD
[ "$TARGET_DIR" == "" ] && TARGET_DIR=${WORK_DIR}/tftpboot
RELEASE=bionic
NETBOOT_DISCOVERY_DIR=$(dirname $0)/../netboot-discovery

# test -d $TARGET_DIR/pxelinux.cfg || { echo "Error: Missing $TARGET_DIR/pxelinux.cfg."; exit 1; }
mkdir -p $TARGET_DIR/pxelinux.cfg

for F in vmlinuz initrd filesystem.squashfs; do
	if ! test -f $TARGET_DIR/pyfounder-discovery/$F; then
		mkdir -p $TARGET_DIR/pyfounder-discovery
		test -f ../netboot-discovery/image/$F || \
			{ echo "Error: ../netboot-discovery/image/$F not found."; exit 1; }
		cp ${NETBOOT_DISCOVERY_DIR}/image/$F $TARGET_DIR/pyfounder-discovery/$F
	fi
done

NETBOOT_TAR_GZ_URL=http://archive.ubuntu.com/ubuntu/dists/${RELEASE}-updates/main/installer-amd64/current/images/netboot/netboot.tar.gz

NETBOOT_TAR_GZ=${WORK_DIR}/download/${RELEASE}-netboot.tar.gz

GRUB2_URL=http://archive.ubuntu.com/ubuntu/dists/${RELEASE}/main/uefi/grub2-amd64/current/grubnetx64.efi

GRUB2_IMAGE=${WORK_DIR}/download/grubnetx64.efi

mkdir -p ${WORK_DIR}/download

if [ ! -f $NETBOOT_TAR_GZ ]; then
	wget -O $NETBOOT_TAR_GZ $NETBOOT_TAR_GZ_URL
fi

if [ ! -f $GRUB2_IMAGE ]; then
	wget -O $GRUB2_IMAGE $GRUB2_URL
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


if [ ! -f $TARGET_DIR/pxelinux.cfg/${RELEASE}-installer ]; then
# installer file
cat << EOF >$TARGET_DIR/pxelinux.cfg/${RELEASE}-installer
default install
timeout 0
LABEL install
        kernel ${RELEASE}/ubuntu-installer/amd64/linux
        append vga=normal initrd=${RELEASE}/ubuntu-installer/amd64/initrd.gz locale=en_US.UTF-8 debian-installer/keymap=us pkgsel/install-language-support=false netcfg/dhcp_timeout=120 console-setup/layoutcode=us console-setup/ask_detect=false
EOF

fi

if [ ! -f $TARGET_DIR/pxelinux.cfg/default ]; then
	cp $TARGET_DIR/pxelinux.cfg/${RELEASE}-installer $TARGET_DIR/pxelinux.cfg/default
fi

# UEFI / GRUB2
mkdir -p $TARGET_DIR/grub/x86_64-efi

if [ ! -f $TARGET_DIR/grub/x86_64-efi/grubnetx64.efi ]; then
	cp $GRUB2_IMAGE $TARGET_DIR/grub/x86_64-efi/grubnetx64.efi
fi

if [ ! -e $TARGET_DIR/grubx64.efi ]; then
	(
	cd $TARGET_DIR
	ln -s grub/x86_64-efi/grubnetx64.efi grubx64.efi
	)
fi

if [ ! -f ${WORK_DIR}/download/grub-pc-bin*amd64.deb ]; then
	cd ${WORK_DIR}/download
	apt download grub-pc-bin
fi

if [ ! -f ${WORK_DIR}/download/grub-pc-bin/usr/lib/grub/i386-pc/regexp.mod ]; then
	mkdir -p ${WORK_DIR}/download/grub-pc-bin
	D=$(ls -1 ${WORK_DIR}/download/grub-pc-bin*amd64.deb | tail -1)
	dpkg -x $D ${WORK_DIR}/download/grub-pc-bin
fi

if [ ! -f $TARGET_DIR/grub/x86_64-efi/regexp.mod ]; then
	cp ${WORK_DIR}/download/grub-pc-bin/usr/lib/grub/i386-pc/regexp.mod $TARGET_DIR/grub/x86_64-efi/regexp.mod
fi

if [ ! -f $TARGET_DIR/grub/grub.cfg ]; then
	cat << EOF >$TARGET_DIR/grub/grub.cfg
# pyfounder example grub.cfg

insmod regexp
regexp --set=1:m1 --set=2:m2 --set=3:m3 --set=4:m4 --set=5:m5 --set=6:m6 '^([0-9a-f]{1,2})\:([0-9a-f]{1,2})\:([0-9a-f]{1,2})\:([0-9a-f]{1,2})\:([0-9a-f]{1,2})\:([0-9a-f]{1,2})' "\$net_default_mac"
mac=\${m1}-\${m2}-\${m3}-\${m4}-\${m5}-\${m6}

menuentry '${RELEASE} installer' -id ${RELEASE}_installer {
    linux ${RELEASE}/ubuntu-installer/amd64/linux vga=normal initrd=${RELEASE}/ubuntu-installer/amd64/initrd.gz locale=en_US.UTF-8 debian-installer/keymap=us pkgsel/install-language-support=false netcfg/dhcp_timeout=120 console-setup/layoutcode=us console-setup/ask_detect=false
    initrd ${RELEASE}/ubuntu-installer/amd64/initrd.gz
}
EOF

fi

echo setup-tftpboot ... done.
