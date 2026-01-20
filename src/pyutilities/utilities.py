#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
# import string
import re


def is_valid_var(var_name: str) -> bool:
    """ 检查变量名是否符合 Python 标识符规则

    Args:
        var_name (str)：待检查的变量名

    Returns:
        bool, True=合法，False=非法
    """
    # 空字符串直接返回非法
    if not var_name:
        return False
    # 首字符必须是字母或下划线
    if var_name[0].isalpha() or var_name[0] == "_":
        for a in var_name[1: ]:
            # 后续字符必须是字母、数字或下划线
            if not(a.isalnum() or a == "_"):
                return False
        return True
    return False


def hex_str_int(hex_str: str, size_byte: int = -1, is_sgn: bool = False) -> int:
    """ 将十六进制字符串转换为整数，支持有符号整数转换

    Args:
        hex_str (__type__)：待转换的十六进制字符串（如 "1A"、"FF"）；
        size_byte (__type__)：字节数（仅在 is_sgn=True 时生效）；
        is_sgn (__type__)：是否转换为有符号整数。

    Returns:
        int, 转换后的整数
    """
    data = int(hex_str, 16)
    if is_sgn:
        # 计算该字节数的最大值
        max_val = 1 << (size_byte * 8)
        # 若数值 ≥ 最大值的一半，说明是负数，需减去最大值
        if data >= max_val/2:
            data -= max_val
    return data


def hex_lst_to_int(hex_lst: list[int], is_sgn: bool = False) -> int:
    """ 十六进制单字节列表转整数（支持有符号转换）

    Args:
        hex_lst (__type__)：单字节整数列表（每个元素0-255，非空）（如 [0x1A, 0x2B]）；
        size_byte (__type__)：字节数（必须>0且等于hex_lst长度）
        is_sgn (__type__)：是否转换为有符号整数。

    Returns:
        int, 转换后的整数

    Raises:
        ValueError: hex_lst为空 或 元素超出0-255范围
    """
    # 输入合法性校验
    if not hex_lst:
        raise ValueError("hex_lst cannot be empty")
    for val in hex_lst:
        if not (0 <= val <= 255):
            raise ValueError(f"hex_lst element {val} out of range (0-255)")

    # 按字节位权累加得到无符号整数
    unsigned_int = 0
    size_byte = len(hex_lst)
    for i, val in enumerate(hex_lst):
        unsigned_int += (val << (8 * (size_byte - i - 1)))

    if is_sgn:
        max_val = 1 << (size_byte * 8)
        if unsigned_int >= max_val/2:
            unsigned_int -= max_val
    return unsigned_int


def int_lst_to_str(hex_lst: list[int]) -> str:
    """ 单字节整数列表转大写十六进制字符串（不足两位补 0）

    Args:
        hex_lst (__type__)：单字节整数列表（0-255）

    Returns:
        str, 大写十六进制字符串（如[10,255]→"0AFF"）
    """
    hex_str = ""
    for val in hex_lst:
        hex_str += f"{val:02X}"
    return hex_str


def legal_name(filename: str) -> str:
    """ 文件名合法化：替换非法字符为下划线
        https://deepinout.com/python/python-qa/167_python_turn_a_string_into_a_valid_filename.html
        合法字符：字母/数字/下划线/点/横线/中文/括号；非法字符：<>:"/\\|*? 

    Args:
        filename (__type__)：原始文件名

    Returns:
        str, 合法文件名
    """
    invalid_chars = r'[<>:"/\\|*?]'
    valid_filename = re.sub(invalid_chars, '_', filename)
    return valid_filename


def current_platform() -> str:
    """ Get current platform name by short string

    Returns:
        linux/mac/win64/win32

    Raises:
        OSError: 不支持的平台
    """
    if sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('darwin'):
        return 'mac'
    elif sys.platform.startswith('win') or sys.platform.startswith('msys') or sys.platform.startswith('cyg'):
        if sys.maxsize > 2 ** 31 - 1:
            return 'win64'
        return 'win32'
    else:
        raise OSError(f"Unsupported platform: {sys.platform}")
