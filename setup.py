#!/usr/bin/python3

from distutils.core import setup
setup(
    name='tiliado-repositories',
    version='0.3.3',
    packages=['tiliadoweb', 'tiliadoweb.config'],
    scripts=['tiliado-repositories'],
    data_files=[("share/applications", ["tiliado-repositories.desktop"])],
    )
