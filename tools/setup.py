#!/usr/bin/env python
"""
TODO: Description and Lisence

@author: Brendan Johan Lee
@contact: brendan@vanntett.net
@version: 1.0
"""
from distutils.core import setup

setup(name = 'opengsmloc tools',
      version = '0.1',
      description = 'Useful tools not related to the core backend or clients. See README for list and discription of tools',
      author = 'Brendan Johan Lee',
      author_email = 'brendan@vanntett.net',
      url = 'http://opengsmloc.org',
      scripts = ['glocalizer'],
      package_dir = {'': 'modules'},
      packages = ['map', 'gloclib'])
