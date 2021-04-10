#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Mitsuru Nakakawaji <mitsuru@procube.jp>
# MIT License

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
