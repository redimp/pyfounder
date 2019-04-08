# Setup the vitual test setup

## 1.) Install and prepare the tftpboot directory

This downloads the netboot image for ubuntu and installs the
netboot discovery image of pyfounder in the ./tftpboot directory
which is linked to the virtual server.

```
./initialize_tftpboot.sh
```

## 2.) Start the server using vagrant

```
vagrant up server
```

The virtual machine will be set up and provisioned using the script
`vagrant_provision_server.sh`. When the server is up and running, you can access it via
<http://10.0.10.10:5000/>.

## 3.) Boot the (empty) client

```
vagrant up client
```

# Working in the virtual test environment

You can access the server using `vagrant ssh server`. There is the pyfounder flask server running in a screen session, for easier development:
```
sudo screen -r
```

The pyfounder root directory is mounted into `/pyfounder` and installed using `pip install --editable`.

The virtual-test-setup directory can be found in `/vagrant`. The config files `server-settings.cfg` and `server-hosts.yaml` can be edited on the host machine.

# Uninstall the virtual test setup

To stop the virtual machines and delete all data use

```
vagrant destroy
```
