#/bin/bash
set -x
set -e
apt-get update
apt-get install --no-install-recommends -y linux-image-amd64 \
    live-boot \
    systemd-sysv
apt-get install  --no-install-recommends -y lvm2 vim-tiny curl openssh-client net-tools \
    isc-dhcp-client less rsync tar gzip parted iputils-ping nmap \
    util-linux psmisc python3-minimal python3-requests python3-psutil python3-urwid \
    lshw python3-yaml util-linux
# apt-get install -y acpid mandb mc

if ! test -e /usr/bin/vim && test -e /usr/bin/vim.tiny; then
    ln -s /usr/bin/vim.tiny /usr/bin/vim
fi

apt-get install -y locales
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
locale-gen --purge en_US.UTF-8 UTF-8

# root auto login
sed -i '/^ExecStart/c\ExecStart=-/sbin/agetty --noclear -a root %I $TERM' /lib/systemd/system/getty\@.service

cat << EOF >/tmp/rc.local
#!/bin/bash
/scripts/startup.sh
EOF

cp /tmp/rc.local /etc/rc.local
chmod +x /etc/rc.local

# see https://raymii.org/s/tutorials/Run_software_on_tty1_console_instead_of_login_getty.html

mkdir -p /etc/systemd/system/getty@tty1.service.d/

cat << EOF >/etc/systemd/system/getty@tty1.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/scripts/pyfounder-discover
StandardInput=tty
StandardOutput=tty
EOF
