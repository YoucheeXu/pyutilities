#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
# import string
import re


def is_illegal_var(var_name: str) -> bool:
    if var_name[0].isalpha() or var_name[0] == "_":
        for a in var_name[1: ]:
            if not(a.isalnum() or a == "_"):
                return False
        return True
    return False


def hex_str_int(hex_str: str, size_byte: int = -1, is_sgn: bool = False) -> int:
    data = int(hex_str, 16)
    if is_sgn:
        max_val = 1 << (size_byte * 8)
        if data >= max_val/2:
            data -= max_val
    return data


def hex_lst_to_int(hex_lst: list[int], size_byte: int = -1, is_sgn: bool = False) -> int:
    unsigned_int = 0
    for i, val in enumerate(hex_lst):
        unsigned_int += (val << (8 * (size_byte - i - 1)))
    # unsignedInt = int(hexStr, 16)
    if is_sgn:
        data = unsigned_int - (1 << (size_byte * 8))
    else:
        data = unsigned_int
    return data


def int_lst_to_str(hex_lst: list[int]) -> str:
    hex_str = ""
    for val in hex_lst:
        hex_str += f"{val:02X}"
    return hex_str


def legal_name(filename: str) -> str:
    """ https://deepinout.com/python/python-qa/167_python_turn_a_string_into_a_valid_filename.html
    """
    # new_name = ''.join(c for c in filename if c in string.ascii_letters + string.digits + '_.-')
    invalid_chars = r'[<>:"/\|*?.]'
    # invalid_chars = r'[^\w\s.-_（）]'
    valid_filename = re.sub(invalid_chars, '_', filename)
    return valid_filename


def current_platform() -> str:
    """
        Get current platform name by short string
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


if __name__ == "__main__":
    import const
    from logit import pv
    const.PI = 3.141596
    pv(const.PI)

    const.PI = 3
    pv(const.PI)
