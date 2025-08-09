#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
from threading import RLock

try:
    from logit import pv
except ImportError:
    from pyutilies.logit import pv


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
class _const:
    class ConstError(PermissionError):
        pass
    class ConstCaseError(TypeError):
        pass

    def __setattr__(self, name: str, value):
        if name in self.__dict__:
            raise self.ConstError(f"Can't change const {name}.")
        if not name.isupper():
            raise self.ConstCaseError(f"const name {name} is not all uppercase")
        self.__dict__[name] = value

    def __delattr__(self, name: str):
        if name in self.__dict__:
            raise self.ConstError(f"Can't unbind const {name}")
        raise NameError(name)


sys.modules[__name__] = _const()
