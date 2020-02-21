# pyfounder virtual test setup (using qemu)

## Prerequisites

* run `script/bootstrap.sh`
* check that you are in the `kvm` group, using `groups`. if not logout and login again.
* make sure your current directory is writeable by root, if not set the `WORK_DIR` environment variable e.g. `export WORK_DIR=/tmp`
* setup the tfpboot directory: `./setup-tfpboot.sh`


## Running the environment

* setup the server: `./setup-server.sh`
* boot the server `./boot-server.sh`

## Random development notes. Stop reading here.

### mount host filesystem from guest

```
mount -t 9p -o trans=virtio tmp /mnt/ -oversion=9p2000.L
```

### links

* https://wiki.qemu.org/Documentation/Networking
* [qemu smb bug](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=747636)
* [qemu p9](https://wiki.qemu.org/Documentation/9psetup#Starting_the_Guest_directly)

### check if client is asking for pxe

```
root@server# tcpdump -vv -i eth1
```
