#!/bin/bash
set -x -e
export DEBIAN_FRONTEND=noninteractive
apt-get -y remove locales
apt-get -y clean
apt-get -y autoclean
apt-get -y autoremove
rm -rf /var/cache/apt/*
rm -rf /var/lib/apt/*
