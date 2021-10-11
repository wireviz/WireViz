#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

from src.wireviz import __version__, CMD_NAME, APP_URL

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name=CMD_NAME,
    version=__version__,
    author='Daniel Rojas',
    #author_email='',
    description='Easily document cables and wiring harnesses',
    long_description=read(os.path.join(os.path.dirname(__file__), 'docs/README.md')),
    long_description_content_type='text/markdown',
    install_requires=[
        'pyyaml',
        'pillow',
        'graphviz',
        ],
    license='GPLv3',
    keywords='cable connector hardware harness wiring wiring-diagram wiring-harness',
    url=APP_URL,
    package_dir={'': 'src'},
    packages=find_packages('src'),
    entry_points={
        'console_scripts': ['wireviz=wireviz.wireviz:main'],
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        ],

)
