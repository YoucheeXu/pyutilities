#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
from threading import RLock

try:
    from logit import pv
except ImportError:
    from pyutilities.logit import pv


single_lock = RLock()

def singleton(cls):
    instance = {}

    def _singleton_wrapper(*args, **kwargs):
        with single_lock:
            if cls not in instance:
                instance[cls] = cls(*args, **kwargs)
        return instance[cls]

    return _singleton_wrapper


@singleton
class gvar:
    pass

sys.modules[__name__] = gvar()

gvar().ver = "0.1.0"
