#!/usr/bin/env python
# -- coding: utf-8 --

import setuptools

try:
    import multiprocessing  # noqa
except ImportError:
    pass

setuptools.setup(
    setup_requires=['pbr'],
    data_files=[('/etc/spamostack', ['etc/conf.json'])],
    pbr=True)