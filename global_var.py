#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# from typing import Any
try:
    from logit import pv
except ImportError:
    from pyutilies.logit import pv


_global_dict: dict[str, object] = {}


def _init():  # 初始化
    # global _global_dict
    _global_dict = {}


def set_value(key: str, value: object):
    # 定义一个全局变量
    _global_dict[key] = value


def get_value(key: str):
    return _global_dict[key]


_init()


if __name__ == '__main__':
    import math
    set_value("var1", "myName")
    pv(get_value("var1"))
    set_value("var2", 3.1415926)
    pv(get_value("var2"))
    var3 = [x * x for x in range(1, 11)]
    set_value("var3", var3)
    pv(get_value("var3"))
    var4 = {math.sqrt(num): num for num in var3}
    set_value("var4", var4)
    pv(get_value("var4"))
