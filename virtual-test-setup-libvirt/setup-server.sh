#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

# SETTINGS

IMAGE_DIR=$(dirname $0)/images
SERVER_IMAGE=$IMAGE_DIR/server.qcow2
SERVER_IMAGE_SIZE=20G
ARCH=amd64
TARGET_ROOT=/tmp/mnt_server
# Network Block Device to use:
NBD=/dev/nbd0

QEMU_NBD="sudo qemu-nbd"

if [ "$1" == "clean" ]; then
    sudo umount $TARGET_ROOT
    $QEMU_NBD -d ${NBD}
    rm -f $SERVER_DISK
    exit 0
fi

set -e

# helper functions
fatal()
{
    echo "Error ${*}" >&2
    exit 1
}

# install requirements
#sudo apt-get install -y debootstrap fdisk qemu-utils
sudo modprobe nbd max_part=16

# test if all tools exists
for TOOL in sfdisk qemu-nbd; do
    [ "$(which ${TOOL})" == "" ] && fatal "${TOOL} not found."
done

mkdir -p $(dirname $SERVER_IMAGE)

# failsafe: disconnect nbd device
$QEMU_NBD -d $NBD &>/dev/null || true

# create image
qemu-img create -f qcow2 $SERVER_IMAGE $SERVER_IMAGE_SIZE

# connect image
$QEMU_NBD -c $NBD $SERVER_IMAGE

# write image partition table
sudo sfdisk $NBD <<EOF
label: dos
start=2048, size=2194304, type=82
,,83
EOF

sudo mkswap ${NBD}p1
sudo mkfs.ext4 ${NBD}p2
mkdir -p $TARGET_ROOT
sudo mount ${NBD}p2 $TARGET_ROOT

# run debootstrap
sudo debootstrap --arch=${ARCH} --variant=minbase stretch $TARGET_ROOT \
    http://ftp.de.debian.org/debian/

sudo mount --bind /dev/ $TARGET_ROOT/dev
sudo mount -t proc none $TARGET_ROOT/proc
sudo mount -t sysfs none $TARGET_ROOT/sys

sudo chroot $TARGET_ROOT apt-get install -y --allow-unauthenticated linux-image-amd64 grub
sudo chroot $TARGET_ROOT grub-install /dev/nbd0
sudo chroot $TARGET_ROOT update-grub
sudo umount $TARGET_ROOT/proc/ $TARGET_ROOT/sys/ $TARGET_ROOT/dev/

sudo grub-install /dev/nbd0 --root-directory=$TARGET_ROOT --modules="biosdisk part_msdos"

# update menu.lst
sudo sed -i -e 's#/dev/nbd0p2#/dev/sda2#' -e 's#/dev/nbd0#/dev/sda#' \
    /tmp/mnt_server/boot/grub/menu.lst


