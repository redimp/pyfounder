#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

SERVER_IMAGE=$PWD/images/server.qcow2
ARCH=amd64
TARGET_ROOT=$PWD/server_root
TARGET_HOSTNAME=server

mkdir -p $TARGET_ROOT
mkdir -p $(dirname $SERVER_IMAGE)

test -f ${TARGET_ROOT}/bin/bash || {
    sudo debootstrap --arch=${ARCH} \
        --include vim,dnsmasq,ifupdown,openssh-server,iputils-ping,isc-dhcp-client,bash,init,net-tools,linux-image-${ARCH} \
        --variant=minbase stretch $TARGET_ROOT \
        http://ftp.de.debian.org/debian/
}

# set root passwd
echo 'root:pyfounder' | sudo chroot "$TARGET_ROOT" chpasswd

# create fstab
cat << EOF | sudo tee "${TARGET_ROOT}/etc/fstab"
/dev/sda / ext4 errors=remount-ro,acl 0 1
EOF

# set hostname
echo ${TARGET_HOSTNAME} | sudo tee "$TARGET_ROOT/etc/hostname"

sudo cp ./configure-server.sh $TARGET_ROOT/

sudo chroot $TARGET_ROOT /bin/bash -x /configure-server.sh
read
# #
# sudo chroot $TARGET_ROOT /bin/bash -c "/bin/systemctl disable apt-daily.timer"
# 
# cat << EOF | sudo tee "${TARGET_ROOT}/etc/network/interfaces.d/default"
# auto lo
# iface lo inet loopback
# 
# auto eth0
# iface eth0 inet dhcp
# 
# auto eth1
# iface eth1 inet static
#     address 10.0.70.1
#     netmask 255.255.255.0
# EOF

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

qemu-system-x86_64 \
  -append 'console=ttyS0 root=/dev/sda net.ifnames=0 biosdevname=0 ipv6.disable=1' \
  -drive "file=${SERVER_IMAGE},format=qcow2" \
  -enable-kvm \
  -serial mon:stdio \
  -m 512M \
  -kernel "$TARGET_ROOT/vmlinuz" \
  -initrd "$TARGET_ROOT/initrd.img" \
  -net user,smb=$PWD/.. \
  -device virtio-rng-pci \
  -device e1000,netdev=n0,mac=52:54:98:76:54:33 \
  -netdev user,id=n0,net=10.0.69.0/24 \
  -device e1000,netdev=n1,mac=52:54:98:76:54:34 \
  -netdev socket,mcast=230.0.0.1:1234,id=n1 \
;
