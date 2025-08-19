#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys

try:
    from singleton import singleton
except ImportError:
    from pyutilies.singleton import singleton


@singleton
class gvar:
    pass

sys.modules[__name__] = gvar()

gvar().ver = "0.1.0"
