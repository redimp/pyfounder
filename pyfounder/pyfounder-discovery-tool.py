#!/usr/bin/env python3

from __future__ import print_function

import os
import sys
import re

from subprocess import getstatusoutput

import json
from yaml import load, dump, add_representer
try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

Dumper.org_represent_str = Dumper.represent_str

def repr_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
    return dumper.org_represent_str(data)

add_representer(str, repr_str, Dumper=Dumper)

def cpu_model():
    try:
        with open('/proc/cpuinfo') as f:
            cpuinfo = f.read()
        cpu_model = re.findall("^model name\s*: (.*)$",cpuinfo,re.MULTILINE)[0]
        return cpu_model
    except:
        return '?'

def ram_kbytes():
    try:
        with open('/proc/meminfo') as f:
            meminfo = f.read()
        memtotalkb = re.findall("^MemTotal:\s*(\d*) kB$",meminfo,re.MULTILINE)[0]
        return int(memtotalkb)
    except:
        return '?'

def get_mac(interface):
    try:
        mac = open('/sys/class/net/'+interface+'/address').readline()
    except:
        mac = "00:00:00:00:00:00"
    return mac[0:17]

def get_ip(interface):
    status, output = getstatusoutput("ip addr show dev {}".format(device))
    try:
        ip = re.findall("inet ([0-9\.])",output,re.MULTILINE)[0]
    except:
        ip = '?'
    return ip

def get_primary_network_interface():
    # ip route list | grep default | ...
    status, output = getstatusoutput("ip route list | grep default")
    if status > 0:
        return '?'
    interface = re.findall("dev\s+([a-zA-Z0-9]+)", output)[0]
    return interface

def ram_bytes():
    return ram_kbytes() * 1024

def lsblk():
    status, output = getstatusoutput("lsblk --raw -n --output NAME,SIZE,ROTA,TYPE | grep 'disk$'")
    # parse output
    data = {}
    try:
        for line in output.splitlines():
            col = line.split()
            ssdhdd = 'hdd'
            if col[2] == '0': ssdhdd = 'ssd'
            data[col[0]]=[col[1],ssdhdd]
    except:
        return None

    return data

def sfdisk(disk):
    status, output = getstatusoutput("sfdisk --dump /dev/{}".format(disk))
    if status != 0:
        return '?'
    return output

def lspci():
    status, output = getstatusoutput("lspci")
    if status != 0:
        return '?'
    return output

def serialnumber():
    status, output = getstatusoutput('dmidecode -t 1 | grep "Serial Number"')
    if status != 0:
        return '?'
    serial = re.findall("Serial Number:\s*([^\s]+)", output)[0]
    return serial

data = {}
data["cpu_model"]     = cpu_model()
data["ram_bytes"]     = ram_bytes()
data["mac"]           = get_mac(get_primary_network_interface())
data["lspci"]         = lspci()
data["serialnumber"]  = serialnumber()
# disk info
_lsblk = lsblk()
data["lsblk"]         = _lsblk or '?'
# sfdisk partition info
data['sfdisk']        = {}
if _lsblk is not None:
    for disk in _lsblk.keys():
        data['sfdisk'][disk] = sfdisk(disk)
# print data as yaml
print(dump(data, Dumper=Dumper))
