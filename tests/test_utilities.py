#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    uv run pytest --cov=src.pyutilities.utilities .\tests\test_utilities.py -v
"""
import sys
import pytest

from src.pyutilities.utilities import (
    is_valid_var,
    hex_str_int,
    hex_lst_to_int,
    int_lst_to_str,
    legal_name,
    current_platform
)


# ---------------------- 测试 is_illegal_var ----------------------
@pytest.mark.parametrize("var_name, expected", [
    # 合法变量名（函数返回True）
    ("_var123", True),
    ("varName", True),
    ("V123_", True),
    # 非法变量名（函数返回False）
    ("123var", False),  # 首字符是数字
    ("var-123", False), # 包含减号
    ("var*name", False),# 包含星号
    ("", False),        # 空字符串（边界场景）
    ("var name", False) # 包含空格
])
def test_is_valid_var(var_name: str, expected: bool) -> None:
    """测试变量名合法性检查（注意函数名与逻辑相反）"""
    assert is_valid_var(var_name) == expected

# ---------------------- 测试 hex_str_int ----------------------
@pytest.mark.parametrize("hex_str, size_byte, is_sgn, expected", [
    # 无符号转换
    ("1A", -1, False, 26),
    ("FF", 1, False, 255),
    ("1A2B", 2, False, 6699),
    # 有符号转换（1字节）
    ("7F", 1, True, 127),   # 小于128，正数
    ("80", 1, True, -128),  # 等于128，负数
    ("FF", 1, True, -1),    # 255 → 255-256=-1
    # 有符号转换（2字节）
    ("7FFF", 2, True, 32767),
    ("8000", 2, True, -32768),
])
def test_hex_str_int(hex_str: str, size_byte: int, is_sgn: bool, expected: int) -> None:
    """测试十六进制字符串转整数（含无符号/有符号）"""
    assert hex_str_int(hex_str, size_byte, is_sgn) == expected

# ---------------------- 测试 hex_lst_to_int ----------------------
@pytest.mark.parametrize("hex_lst, is_sgn, expected", [
    # 2字节无符号：[0x1A,0x2B] → 0x1A2B=6699
    ([0x1A, 0x2B], False, 0x1A2B),
    # 1字节无符号：[0xFF] → 255
    ([0xFF], False, 255),
    # 1字节有符号：[0xFF] → -1
    ([0xFF], True, -1),
    # 1字节有符号：[0x80] → -128
    ([0x80], True, -128),
    # 2字节有符号：[0x7F,0xFF] → 0x7FFF=32767
    ([0x7F, 0xFF], True, 32767),
    # 2字节有符号：[0x80,0x00] → -32768
    ([0x80, 0x00], True, -32768),
])
def test_hex_lst_to_int(hex_lst: list[int], is_sgn: bool, expected: int) -> None:
    """测试十六进制列表转整数（含无符号/有符号）"""
    assert hex_lst_to_int(hex_lst, is_sgn) == expected

# 测试输入合法性校验
def test_hex_lst_to_int_invalid_input() -> None:
    # 空列表
    with pytest.raises(ValueError, match="hex_lst cannot be empty"):
        hex_lst_to_int([], False)
    # 元素超出0-255范围
    with pytest.raises(ValueError, match="hex_lst element 32767 out of range \(0-255\)"):
        hex_lst_to_int([32767], False)

# ---------------------- 测试 int_lst_to_str ----------------------
@pytest.mark.parametrize("hex_lst, expected", [
    ([10, 255], "0AFF"),
    ([1, 2, 3], "010203"),
    ([0, 16], "0010"),
    ([255, 0], "FF00"),
    ([], ""),  # 空列表
])
def test_int_lst_to_str(hex_lst: list[int], expected: str) -> None:
    """测试十六进制列表转大写字符串（补两位）"""
    assert int_lst_to_str(hex_lst) == expected

# ---------------------- 测试 legal_name ----------------------
@pytest.mark.parametrize("filename, expected", [
    ("test.txt", "test.txt"),  # 合法文件名, .保留，不再被替换
    ("test<file>.txt", "test_file_.txt"),  # 替换<和>
    ("test:file\\/|*.txt", "test_file____.txt"),  # 替换所有非法字符
    ("test?.txt", "test_.txt"),  # 替换?
    ("", ""),  # 空字符串
    ("合法文件名_（）.txt", "合法文件名_（）.txt"),  # 中文/括号合法
])
def test_legal_name(filename: str, expected: str) -> None:
    """测试文件名合法化（替换非法字符为下划线）"""
    assert legal_name(filename) == expected

# ---------------------- 测试 current_platform ----------------------
def test_current_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """测试平台检测（使用monkeypatch模拟不同平台）"""
    # 模拟Linux
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "maxsize", 9223372036854775807)
    assert current_platform() == "linux"

    # 模拟macOS
    monkeypatch.setattr(sys, "platform", "darwin")
    assert current_platform() == "mac"

    # 模拟Windows 64位
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "maxsize", 9223372036854775807)  # 64位maxsize
    assert current_platform() == "win64"

    # 模拟Windows 32位
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "maxsize", 2147483647)  # 32位maxsize
    assert current_platform() == "win32"

    # 模拟不支持的平台
    monkeypatch.setattr(sys, "platform", "freebsd")
    with pytest.raises(OSError) as exc_info:
        current_platform()
    assert "Unsupported platform: freebsd" in str(exc_info.value)
