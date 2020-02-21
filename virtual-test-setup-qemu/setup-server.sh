#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

[ "$WORK_DIR" == "" ] && WORK_DIR=$PWD
[ "$SERVER_IMAGE" == "" ] && SERVER_IMAGE=$WORK_DIR/images/server.qcow2
[ "$TARGET_ROOT" == "" ] && TARGET_ROOT=$WORK_DIR/server_root
ARCH=amd64
TARGET_HOSTNAME=server
SCRIPTS_DIR=$(dirname $0)/scripts

mkdir -p $TARGET_ROOT
mkdir -p $(dirname $SERVER_IMAGE)

test -f ${TARGET_ROOT}/bin/bash || {
    sudo debootstrap --arch=${ARCH} \
        --include gnupg2,vim,dnsmasq,ifupdown,openssh-server,iputils-ping,isc-dhcp-client,bash,init,net-tools,linux-image-${ARCH} \
        --variant=minbase stretch $TARGET_ROOT \
        http://ftp.de.debian.org/debian/
}

# set root passwd
echo 'root:pyfounder' | sudo chroot "$TARGET_ROOT" chpasswd

# set hostname
echo ${TARGET_HOSTNAME} | sudo tee "$TARGET_ROOT/etc/hostname"

sudo cp $SCRIPTS_DIR/configure-server.sh $TARGET_ROOT/

sudo chroot $TARGET_ROOT /bin/bash -x /configure-server.sh

sudo chown -R root:root ${TARGET_ROOT}

test -f $SERVER_IMAGE || {
    # create image
    sudo virt-make-fs \
        --format qcow2 \
        --size +1G \
        --type ext2 \
        "$TARGET_ROOT" \
        "$SERVER_IMAGE" \
      ;
    sudo chmod 666 "$SERVER_IMAGE"
}

