import os
import sys

from src.pyutilities.pyexcel_win32com import Excel

import shutil

# filepath = r"你的文档路径"
# main(filepath)

path = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    path = os.path.dirname(os.path.abspath(sys.executable))

source_file = os.path.join(path, "resources", "template.xlsx")
dest_file = os.path.join(path, "resources", "logs", "123.xlsx")

try:
    _ = shutil.copyfile(source_file, dest_file)
except IOError as e:
    print("Unable to copy file. %s" % e)

excel = Excel(dest_file)

new_sheet = "ISG_26_01"
ws = excel.copy_sheet("ISG", new_sheet)

start_index_adr = "E3"      # E3
single_gap_adr = 2,2        # B2
line_gap_adr = 2, 1         # A2
frame_adr = 3, 1            # A3

data_isg = os.path.join(path, "resources", "data_isg.txt")
with open(data_isg, 'r', encoding='utf-8') as f:
    data = f.read()

# ws.set_cell(*start_index_adr, 28)
ws.set_cell(start_index_adr, 28)
ws.set_cell(single_gap_adr, 3)
ws.set_cell(line_gap_adr, 190)
ws.set_cell(frame_adr, data)

new_sheet = "TM_25_01"
ws = excel.copy_sheet("TM", new_sheet)

data_tm = os.path.join(path, "resources", "data_tm.txt")
with open(data_tm, 'r', encoding='utf-8') as f:
    data = f.read()

ws.set_cell(start_index_adr, 28)
ws.set_cell(single_gap_adr, 3)
ws.set_cell(line_gap_adr, 2400)
ws.set_cell(frame_adr, data)

# excel.add_sheet("haha2", 2)
# excel.add_sheet("haha")

# excel.save("haha.xlsx")
# sheets = excel.sheets()
# pv(sheets)
excel.close()

# new_file = os.path.join(path, "resources", "logs", "haha.xlsx")
# excel = Excel()
# excel.new_workbook()
# excel.rename_sheet("sheet1", "sheet99")
# excel.save(new_file)
# excel.close(False)
