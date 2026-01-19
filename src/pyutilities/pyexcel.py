#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import abc
# from typing import overload

# try:
    # from logit import pv
# except ImportError:
    # from pyutilities.logit import pv


class PySheet(abc.ABC):

    @abc.abstractmethod
    def set_cell(self, cell: str | tuple[int, int], val: int | float | str):
        pass

    @abc.abstractmethod
    def get_cell(self, cell: str | tuple[int, int]) -> int | float | str | None:
        pass

    def str_to_tuple(self, cell: str) -> tuple[int, int]:
        cell = cell.upper()
        letters = ""
        digits_str = ""
        alpha_len_old = 0
        alpha_len = 0
        digit_len = 0
        for char_ in cell:
            if char_.isalpha():
                letters += char_
                alpha_len += 1
            elif char_.isdigit():
                digits_str += char_
                digit_len += 1
            else:
                raise ValueError(f"illegal character {char_}")
            if digit_len != 0 and alpha_len > alpha_len_old:
                raise ValueError(f"illegal cell {cell}")
            alpha_len_old = alpha_len
        x = int(digits_str, 10)
        y = 0
        a_digitm1 = ord('A') - 1
        # pv(a_digitm1)
        for i, char_ in enumerate(letters):
            y += ord(char_) - a_digitm1 + (alpha_len - i - 1) * 26
        y -= alpha_len - 1
        return x, y


class PyExcel(abc.ABC):
    def __init__(self, excelfile: str):
        self._excelfile: str = excelfile

    @abc.abstractmethod
    def save(self, newfile: str = ""):
        pass

    @abc.abstractmethod
    def close(self, save: bool = True):
        # 关闭+默认保存当前
        pass

    @abc.abstractmethod
    def copy_sheet(self, src_sheet: str, dest_sheet: str) -> PySheet:
        pass

    @abc.abstractmethod
    def sheets(self) -> list[str]:
        pass

    @abc.abstractmethod
    def add_sheet(self, sheetname: str = "", location: int | None = None) -> PySheet:
        pass

    @abc.abstractmethod
    def get_sheet(self, sheetname: str = "") -> PySheet:
        pass

    @abc.abstractmethod
    def remove_sheet(self, sheetname: str = "") -> bool:
        pass

    @abc.abstractmethod
    def rename_sheet(self, old_sheetname: str, new_sheetname: str) -> bool:
        # sheet重命名
        pass
