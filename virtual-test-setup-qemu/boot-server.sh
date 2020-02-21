#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

[ "$WORK_DIR" == "" ] && WORK_DIR=$PWD
[ "$SERVER_IMAGE" == "" ] && SERVER_IMAGE=$WORK_DIR/images/server.qcow2
[ "$TARGET_ROOT" == "" ] && TARGET_ROOT=$WORK_DIR/server_root
PYFOUNDER_ROOT=$(dirname $0)/..

qemu-system-x86_64 \
  -append 'console=ttyS0 root=/dev/sda net.ifnames=0 biosdevname=0 ipv6.disable=1' \
  -drive "file=${SERVER_IMAGE},format=qcow2" \
  -enable-kvm \
  -serial mon:stdio \
  -m 512M \
  -kernel "$TARGET_ROOT/vmlinuz" \
  -initrd "$TARGET_ROOT/initrd.img" \
  -virtfs local,id=fs0,path=$PYFOUNDER_ROOT,security_model=none,mount_tag=pyfounder \
  -device virtio-rng-pci \
  -device e1000,netdev=n0,mac=52:54:98:76:54:33 \
  -netdev user,id=n0,net=10.0.69.0/24 \
  -device e1000,netdev=n1,mac=52:54:98:76:54:34 \
  -netdev socket,mcast=230.0.0.1:1234,id=n1 \
;
