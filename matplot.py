#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from logit import pv
except:
    from pyutilities.logit import pv


class LineData:
    def __init__(self, yData, legend = "", style = "solid", visible = True):
        self.legend = legend
        self.style = style
        self.yData = yData
        self.visible = visible
        self.line = None

'''
TODO: 
    1. legend           OK
    2. size             OK
    3. grid
'''
class MatPlot:
    __dpi=100
    def __init__(self, frm: tk.Frame, title: str, xLabel: str, yLabel: str, size=(480,160)):

        self.__size = tuple(item / self.__dpi for item in size)
        # print(f"size = {self.__size}")

        self.__xData = None
        self.__LinesData: list[LineData] = []

        self.__yMin = float('inf')
        self.__yMax = float('-inf')

        self.__create(frm, title, xLabel, yLabel)

    def __create(self, frm: tk.Frame, title: str, xLabel: str, yLabel: str):
        fig = plt.Figure(figsize=self.__size, dpi=self.__dpi)
        self.__canvas = FigureCanvasTkAgg(fig, frm)
        self.__ax = fig.add_subplot()
        fig.subplots_adjust(bottom=0.25)        

        self.__ax.set_title(title)
        self.__ax.set_xlabel(xLabel)
        self.__ax.set_ylabel(yLabel)
        self.__ax.grid()
        # self.__ax.legend(loc='upper right')
        self.__ax.autoscale()

    def pack(self, side, fill, expand, padx, pady):
        # ctrl.pack(side=atrDict["pos"], fill=tk.BOTH, expand=True, padx=eval(atrDict["xPad"]), pady=eval(atrDict["yPad"]))
        self.__canvas.get_tk_widget().pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)

    def set_xData(self, xData):
        self.__xData = xData
        # self.__xMin
        # self.__xMax

    def add_line(self, line: LineData, idxLine: int = sys.maxsize):
        # print("linesData:", len(self.__LinesData))
        # print("idxLine:", idxLine)
        yData = line.yData

        if idxLine >= len(self.__LinesData):
            if line.visible:
                line.line, = self.__ax.plot(self.__xData, yData, label=line.legend, linestyle=line.style)
            self.__LinesData.append(line)
            # self.__yMin = min(self.__yMin, min(yData))
            # self.__yMax = max(self.__yMax, max(yData))
        else:
            self.__LinesData[idxLine].yData = yData
            if line.visible:
                self.__LinesData[idxLine].line.set_ydata(yData)

    def show_line(self, idx, show):
        self.__LinesData[idx].visible = show
        line = self.__LinesData[idx].line
        if show:
            if not line:
                line = self.__LinesData[idx]
                self.__LinesData[idx].line, = self.__ax.plot(self.__xData, line.yData, label = line.legend, linestyle = line.style)
        else:
            if line:
                self.__LinesData[idx].line.remove()
                self.__LinesData[idx].line = None
        # self.__LinesData[idx].line.set_visible(show)
        # self.__LinesData[idx].line.get_legend().set_visible(show)

    def update_yData(self, idx: int, yData):
        self.__LinesData[idx].yData = yData
        self.__LinesData[idx].line.set_ydata(yData)

    def __RecalculateAxesScale(self):
        self.__yMin = float('inf')
        self.__yMax = float('-inf')

        for line in self.__LinesData:
            if line.visible:
                yData = line.yData
                self.__yMin = min(self.__yMin, min(yData))
                self.__yMax = max(self.__yMax, max(yData))

        try:
            self.__ax.set_ylim(self.__yMin * 1.05, self.__yMax * 1.05)
        except Exception as r:
            print(r)

    def draw(self):
        self.__RecalculateAxesScale()

        for line in self.__LinesData:
            if(line.legend):
                self.__ax.legend(loc='upper right')
                break
        self.__canvas.draw()


if __name__ == '__main__':

    import numpy as np
    np.seterr(divide='ignore', invalid='ignore')

    def Lst2Ary(lst, dType):
        return np.array(lst).astype(dType)

    rawSinH = Lst2Ary([1410, 2010, 2622, 2988, 2992, 2647, 2091, 1507, 1114, 1065, 1411, 2011, 2622, 2987, 2991, 2646, 2091, 1509, 1114, 1064, 1411, 2011, 2622, 2987, 2990, 2646, 2091, 1508, 1114, 1065, 1411, 2011, 2622, 2987, 2991, 2646, 2091, 1508, 1114, 1065], np.int16)
    
    rawSinL = Lst2Ary([2592, 2005, 1437, 1124, 1163, 1523, 2064, 2607, 2950, 2959, 2595, 2006, 1434, 1120, 1159, 1520, 2063, 2610, 2955, 2959, 2592, 2003, 1434, 1121, 1159, 1522, 2064, 2610, 2954, 2959, 2591, 2004, 1435, 1121, 1160, 1521, 2063, 2609, 2954, 2960], np.int16)

    x = np.linspace(0, 39, 40)

    frmRoot = tk.Tk()

    matPlot = MatPlot(frmRoot, r"Sine Wave", r"Points", r"Sine", (640, 480))
    matPlot.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10), pady=(10, 10))
    matPlot.set_xData(x)
    sinLine1 = LineData(rawSinH, 'rawSinH')
    matPlot.add_line(sinLine1)
    sinLine2 = LineData(rawSinL, 'rawSinL')
    matPlot.add_line(sinLine2)
    matPlot.draw()

    menubar = tk.Menu(frmRoot)

    fileMenu = tk.Menu(menubar, tearoff=False)
    fileMenu.add_command(label="...", command=None)
    fileMenu.add_separator()
    fileMenu.add_command(label="Exit", command=frmRoot.destroy)
    menubar.add_cascade(label="File", menu=fileMenu)

    toolMenu = tk.Menu(menubar, tearoff=False)

    def show_sinH():
        matPlot.show_line(0, showLineSinH.get())
        matPlot.draw()

    def show_sinL():
        matPlot.show_line(1, showLineSinL.get())
        matPlot.draw()

    showLineSinH = tk.BooleanVar()
    showLineSinH.set(True)
    toolMenu.add_checkbutton(label="Show SinH", command=show_sinH, variable=showLineSinH)
    showLineSinL = tk.BooleanVar()
    showLineSinL.set(True)
    toolMenu.add_checkbutton(label="Show SinL", command=show_sinL, variable=showLineSinL)

    menubar.add_cascade(label="Tool", menu=toolMenu)
    
    _ = frmRoot.config(menu=menubar)

    frmRoot.mainloop()
