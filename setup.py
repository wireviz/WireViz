#!/usr/bin/env python3
"""WireViz is a tool for easily documenting wiring harnesses."""


from setuptools import setup, find_packages


setup(

    name='wireviz',
    version='0.0.2',

    author='Daniel Rojas',
    author_email='github@danielrojas.net',
    maintainer='Daniel Rojas',
    maintainer_email='github@danielrojas.net',

    url='',
    description=__doc__,
    long_description=open('README.rst').read(),
    install_requires=open('requirements.txt').read().splitlines(),

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=[
        'scripts/wirewiz',
    ],

    license='GPL',
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ]

)
