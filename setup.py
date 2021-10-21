#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from setuptools import find_packages, setup

from src.wireviz import APP_URL, CMD_NAME, __version__

README_PATH = Path(__file__).parent / "docs" / "README.md"

setup(
    name=CMD_NAME,
    version=__version__,
    author="Daniel Rojas",
    # author_email='',
    description="Easily document cables and wiring harnesses",
    long_description=open(README_PATH).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "click",
        "pyyaml",
        "pillow",
        "graphviz",
    ],
    license="GPLv3",
    keywords="cable connector hardware harness wiring wiring-diagram wiring-harness",
    url=APP_URL,
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={
        "console_scripts": [
            "wireviz=wireviz.wv_cli:wireviz",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
