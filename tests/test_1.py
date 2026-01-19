# import os
# import sys
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(root_path)
from src.pyutilities.logit import pv
from src.pyutilities import gvar
from src.pyutilities import const

gvar.var1 = "hello"
pv(gvar.var1)
pv(gvar.ver)
pv(gvar.global_var_ver)

const.PI = 3.141596
pv(const.PI)

const.PI = 3
pv(const.PI)
