#!/bin/bash

CLIENT_IMAGE=images/client0.qcow2

mkdir -p $(dirname $CLIENT_IMAGE)

qemu-img create -f qcow2 $CLIENT_IMAGE 20G

qemu-system-x86_64 \
  -enable-kvm \
  -drive "file=${CLIENT_IMAGE},format=qcow2" \
  -m 512M \
  -device virtio-rng-pci \
  -boot n \
  -device e1000,netdev=n1,mac=52:54:98:76:54:35 \
  -netdev socket,mcast=230.0.0.1:1234,id=n1 \
