import os
import sys
import shutil

from src.pyutilities.pyexcel_openpyxl import Excel

path = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    path = os.path.dirname(os.path.abspath(sys.executable))

source_file = os.path.join(path, "resources", "template.xlsx")
dest_file = os.path.join(path, "resources", "logs", "123.xlsx")

try:
    _ = shutil.copyfile(source_file, dest_file)
except OSError as e:
    print(f"Unable to copy file, {e}")

excel = Excel(dest_file)
new_sheet = "ISG_26_01"
ws = excel.copy_sheet("ISG", new_sheet)

start_index_adr = "E3"
single_gap_adr = 2, 2       # B2
line_gap_adr = 2, 1         # A2
frame_adr = 3, 1            # A3

data_isg = os.path.join(path, "resources", "data.txt")
with open(data_isg, encoding='utf-8') as f:
    data = f.read()

ws.set_cell(start_index_adr, 28)
ws.set_cell(single_gap_adr, 3)
ws.set_cell(line_gap_adr, 190)
ws.set_cell(frame_adr, data)

excel.close()
