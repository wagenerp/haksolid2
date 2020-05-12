#!/usr/bin/env python3
import sys
from setuptools import setup, find_packages

setup(
  name='haksolid2',
  author='Peter Wagener',
  version='0.1',
  packages=find_packages(where='src'),
  package_dir={'': 'src'},
  extras_require={},
  install_requires=['numpy'],
  url='https://github.com/wagenerp/haksolid2',
  maintainer='Peter Wagener',
  maintainer_email='mail@peterwagener.net',
  python_requires='>=3.5',
)
