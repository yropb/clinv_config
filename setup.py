#!/usr/bin/env python3

from setuptools import setup

setup(
    name='clinv_config',
    version='0.0.1',
    description='Simple configuration management inventory',
    url='https://github.com/yropb/clinv_config',
    author='yropb',
    author_email='yropb@ya.ru',
    license='Mozilla Public License 2.0 (MPL 2.0)',
    packages=[
        'clinv_config',
    ],
    install_requires=[
        'wrapt',
        'tox',
        'flake8',
        'pytest',
    ],
    zip_safe=False)
