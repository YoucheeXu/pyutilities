#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys

from src.pyutilities.singleton import singleton

@singleton
class gvar:
    pass

sys.modules[__name__] = gvar()

gvar().ver = "0.1.0"
