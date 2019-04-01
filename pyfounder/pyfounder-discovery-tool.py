#!/usr/bin/env python3

from __future__ import print_function

import os
import sys
import re

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

def getmac(interface):
    try:
        mac = open('/sys/class/net/'+interface+'/address').readline()
    except:
        mac = "00:00:00:00:00:00"
    return mac[0:17]

def get_primary_network_interface():
    # ip route list | grep default | ...
    return None

def ram_bytes():
    return ram_kbytes() * 1024

print("cpu_model = {}".format(cpu_model()))
print("ram_bytes = {}".format(ram_bytes()))
