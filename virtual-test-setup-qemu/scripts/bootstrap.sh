#!/bin/bash
# vim: set et ts=8 sts=4 sw=4:

set -e

sudo apt-get install -y debootstrap qemu-kvm libguestfs-tools

groups | grep kvm >/dev/null || sudo adduser $USER kvm
