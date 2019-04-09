#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import click
import requests
import yaml

@click.command()
def cli():
    """Example script."""
    click.echo('Hello World!')

if __name__ == "__main__":
    cli()
