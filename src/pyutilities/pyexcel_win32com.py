# !/usr/bin/python3
# -*- coding: utf-8 -*-
""" pyexcel_win32com
"""
import os
from typing import override

import win32com.client as client
# import pythoncom

from src.pyutilities.logit import pv
from src.pyutilities.pyexcel import PySheet, PyExcel


def get_filelist(filepath: str):
    dir_list = os.listdir(filepath)
    return dir_list

# xls = xlwt.Workbook()
# xls.add_sheet("Steady_points")
# xls.save(path_for_results)

def copy_sheet(filepath: str, file_list: list[str]):
    excel = client.Dispatch('Excel.Application')
    excel.visible = 1 # 此行设置打开的Excel表格为a可见状态；忽略则Excel表格默认不可见
    dest_file = excel.Workbooks.Add() #新建立excel文件
    dest_worksheets = dest_file.Worksheets
    for filename in file_list:
        文件名分解 = filename.split('.')
        print(文件名分解)
        if 文件名分解[-1] == 'xlsx' or 文件名分解[-1] == 'xls':
            src_file = excel.Workbooks.Open(filepath + '\\'+ filename)
            表_集合 = src_file.Worksheets
            表_集合(1).Copy(None, dest_worksheets(1)) # 跨表复制, 插入第一个表之后, 记得 Copy 首字母大写
            dest_worksheets(2).Name = 文件名分解[0]  # 由于新表总是在第二个表,所以第二个表改名就可了.
            src_file.Close(SaveChanges=0)
        else:
            pass
    dest_file.SaveAs(filepath + r'\处理后的文件.xlsx')
    dest_file.Close(SaveChanges=0)


def save_something_to_excel(result_file_path):
    excel_app = client.Dispatch('Excel.Application')
    excel_app.Visible = False  # 设置进程界面是否可见 False表示后台运行
    excel_app.DisplayAlerts = False # 设置是否显示警告和消息框
    book = excel_app.Workbooks.Add() # 添加Excel工作簿
    sheet = excel_app.Worksheets(1)  # 获取第一个Sheet
    sheet.name = '汇总统计' # 设置Sheet名称
    sheet.Columns.ColumnWidth = 10  # 设置所有列列宽
    sheet.Columns(1).ColumnWidth = 20 # 设置第1列列宽
    sheet.Rows.RowHeight = 15 # 设置所有行高
    sheet.Rows(1).RowHeight = 20  # 设置第一行行高
    usedRange = sheet.UsedRange  # 获取sheet的已使用范围
    rows = usedRange.Rows.Count  # 获取已使用范围的最大行数，初始值为 1
    cols = usedRange.Columns.Count  # 获取已使用范围的最大列数，初始值为 1
    print(rows, cols) # 输出 1 1
    usedRange.Rows.RowHeight = 30 # 设置已使用范围内的行高
    usedRange.Columns.ColumnWidth = 30 # 设置已使用范围内的列宽
    # do something ...
    row_index = 1
    for index, item in enumerate(['日期', '请求方法', 'URL', '调用次数']):
        # 单元格赋值 sheet.Cells(row_index, col_index).Value = 目标值 row_index, col_index 起始值为1
        sheet.Cells(row_index, index + 1).Value = item
    row_index += 1
    # do something else ...
    usedRange = sheet.UsedRange
    rows = usedRange.Rows.Count
    cols = usedRange.Columns.Count
    print(rows, cols) # 输出 1 4
    sheet.Cells(1, 2).Font.Size = 29  # 设置单元格字体大小
    sheet.Cells(1, 2).Font.Bold = True  # 字体是否加粗 True 表示加粗，False 表示不加粗
    sheet.Cells(2, 2).Font.Name = "微软雅黑" # 设置字体名称
    # sheet.Cells(2, 2).Font.Color = RGB(0, 0, 255) # 设置字体颜色 # 不起作用
    sheet2 = excel_app.Worksheets.Add()  # 添加Sheet页
    sheet2.Activate # 设置默认选中的sheet为sheet2
    sheet3 = excel_app.Worksheets.Add()
    #注意，Move操作，会将被移动的表单(本例中的sheet)设置为默认选中状态，也就是说覆盖 sheet.Activate所做的变更
    sheet.Move(sheet3, None)  # 将sheet移动到sheet3之前
    book.SaveAs(result_file_path) # 注意：结果文件路径必须是绝对路径
    book.Close() # 关闭工作簿
    excel_app.Quit() # 退出


def main(filepath: str):
    文件集 = get_filelist(filepath)
    copy_sheet(filepath, 文件集)
    return


class WorkSheet(PySheet):
    def __init__(self, sheet):
        self._sheet = sheet

    @override
    def set_cell(self, cell: str | tuple[int, int], val: int | float | str):
        x, y = self._str_to_tuple(cell)
        self._sheet.Cells(x, y).Value = val

    @override
    def get_cell(self, cell: str | tuple[int, int]) -> int | float | str | None:
        x, y = self._str_to_tuple(cell)
        return self._sheet.Cells(x, y).Value

    def _str_to_tuple(self, cell: str | tuple[int, int]) -> tuple[int, int]:
        if isinstance(cell, str):
            # cell = cell.upper()
            # x = int(cell[1: ])
            # y = ord(cell[0]) - ord('A') + 1
            x, y = self.str_to_tuple(cell)
        else:
            x = cell[0]
            y = cell[1]
        return x, y


class Excel(PyExcel):
    def __init__(self, excelfile: str = ""):
        super().__init__(excelfile)
        # self._excel_app = client.DispatchEx('Excel.Application')
        self._excel_app = client.Dispatch('Excel.Application')
        self._excel_app.Visible = False  # 设置进程界面是否可见，False表示后台运行
        self._excel_app.DisplayAlerts = False # 设置是否显示警告和消息框

        if excelfile:
            self._workbook = self._excel_app.Workbooks.Open(excelfile)

    def new_workbook(self):
        self._workbook = self._excel_app.Workbooks.Add()

    @override
    def copy_sheet(self, src_sheet: str, dest_sheet: str) -> WorkSheet:
        self._workbook.Worksheets(src_sheet).Copy(None, self._workbook.Worksheets(1))
        new_sheet = self._workbook.Worksheets(2)
        # pv(new_sheet.Name)
        new_sheet.Name = dest_sheet
        return WorkSheet(new_sheet)

    @override
    def sheets(self) -> list[str]:
        return [sht.Name for sht in self._workbook.Worksheets]

    @override
    def add_sheet(self, sheetname: str = "", location: int | None = None) -> WorkSheet:
        ws = self._excel_app.Worksheets.Add()
        ws.Name = sheetname
        if location:
            ws1 = self._excel_app.Worksheets(location)
            ws.Move(ws1, None)  # 将sheet移动到ws1之前
        return WorkSheet(ws)

    @override
    def get_sheet(self, sheetname: str = "") -> WorkSheet:
        return WorkSheet(self._workbook.Worksheets(sheetname))

    @override
    def remove_sheet(self, sheetname: str = "") -> bool:
        pass

    @override
    def rename_sheet(self, old_sheetname: str, new_sheetname: str) -> bool:
        # sheet重命名
        old_worksheet = self._workbook.Worksheets(old_sheetname)
        old_worksheet.Name = new_sheetname
        return True

    @override
    def close(self, save: bool = True):
        if save:
            self.save()
        self._workbook.Close()

    @override
    def save(self, newfile: str = ""):
        if newfile:
            self._workbook.SaveAs(newfile)
        self._workbook.Save()

    def __del__(self):
        self._excel_app.Quit()
