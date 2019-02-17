#!/usr/bin/env python

import yaml
from pprint import pprint

def load_yaml(path):
    try:
        with open(path, 'r') as f:
            return yaml.load(f)
    except (yaml.MarkedYAMLError) as exc:
        print(exc)
    except (IOError, yaml.YAMLError) as exc:
        print(exc)
    return {}

d = load_yaml('config.yaml')
pprint(d)
