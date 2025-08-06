#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
TODO: 
    1. legend           OK
    2. size             OK
    3. grid
"""
import sys
from dataclasses import dataclass, field
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from logit import pv
except ImportError:
    from pyutilities.logit import pv

# from typing import List, Dict, Tuple


@dataclass
class LineData:
    ydata: any
    style_dict: dict = field(default_factory=dict)
    visible: bool = True
    line = None


class MatPlot:
    _dpi = 100
    _xdata = None
    _lines_data: list[LineData] = []

    _ymin: float = float("inf")
    _ymax: float = float("-inf")

    def __init__(
        self,
        frm: tk.Frame,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        size: tuple[int, int] = (640, 480),
    ):

        self._size = tuple(item / self._dpi for item in size)
        # print(f"size = {self._size}")
        self._create(frm, title, xlabel, ylabel)

    def _create(self, frm: tk.Frame, title: str, xlabel: str, ylabel: str):
        fig = plt.Figure(figsize=self._size, dpi=self._dpi)
        self._canvas = FigureCanvasTkAgg(fig, frm)
        self._ax = fig.add_subplot()
        fig.subplots_adjust(bottom=0.25)

        self._ax.set_title(title)
        self._ax.set_xlabel(xlabel)
        self._ax.set_ylabel(ylabel)
        self._ax.grid()
        # self._ax.legend(loc='upper right')
        self._ax.autoscale()

    def pack(self, **pack_dict):
        # ctrl.pack(side=atrDict["pos"], fill=tk.BOTH, expand=True, padx=eval(atrDict["xPad"]), pady=eval(atrDict["yPad"]))
        # self._canvas.get_tk_widget().pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)
        self._canvas.get_tk_widget().pack(**pack_dict)

    @property
    def xdata(self):
        return self._xdata

    @xdata.setter
    def xdata(self, xdata):
        self._xdata = xdata
        # self._xMin
        # self._xMax

    def add_line(self, line: LineData, idx_line: int = sys.maxsize):
        # print("linesData:", len(self._LinesData))
        # print("idxLine:", idxLine)
        ydata = line.ydata

        if idx_line >= len(self._lines_data):
            if line.visible:
                line.line = self._ax.plot(self._xdata, ydata, **line.style_dict)
            self._lines_data.append(line)
        else:
            self._lines_data[idx_line].ydata = ydata
            if line.visible:
                self._lines_data[idx_line].line.set_ydata(ydata)

    def show_line(self, idx: int, is_show: bool):
        self._lines_data[idx].visible = is_show
        line = self._lines_data[idx].line
        if is_show:
            if not line:
                line = self._lines_data[idx]
                (self._lines_data[idx].line,) = self._ax.plot(
                    self._xdata, line.ydata, **line.style_dict
                )
        else:
            if line:
                self._lines_data[idx].line.remove()
                self._lines_data[idx].line = None
        # self._LinesData[idx].line.set_visible(show)
        # self._LinesData[idx].line.get_legend().set_visible(show)

    def update_ydata(self, idx: int, ydata):
        self._lines_data[idx].ydata = ydata
        self._lines_data[idx].line.set_ydata(ydata)

    def _recalculate_axes_scale(self):
        self._ymin = float("inf")
        self._ymax = float("-inf")

        for line in self._lines_data:
            if line.visible:
                ydata = line.ydata
                try:
                    ymin = min(ydata)
                    ymax = max(ydata)
                except Exception as r:
                    # print(r)
                    ymin = ydata.min()
                    ymax = ydata.max()
                finally:
                    pass

                self._ymin = min(self._ymin, ymin)
                self._ymax = max(self._ymax, ymax)

        self._ymin = -0.15 if self._ymin == 0 else self._ymin
        self._ax.set_ylim(self._ymin * 1.05, self._ymax * 1.05)

        self._xmin = float("inf")
        self._xmax = float("-inf")

        try:
            xmin = min(self._xdata)
            xmax = max(self._xdata)
        except Exception as r:
            # print(r)
            xmin = self._xdata.min()
            xmax = self._xdata.max()
        finally:
            pass

        self._xmin = min(self._xmin, xmin)
        self._xmax = max(self._xmax, xmax)

        self._xmin = -0.15 if self._xmin == 0 else self._xmin
        self._ax.set_xlim(self._xmin * 1.05, self._xmax * 1.05)

    def draw(self):
        self._recalculate_axes_scale()

        for line in self._lines_data:
            if line.style_dict.get("label"):
                self._ax.legend(loc="upper right")
                break
        self._canvas.draw()


class Plot:
    def __init__(
        self, title: str = "", num_row: int = 1, num_col: int = 1, **plot_dict
    ):
        self._title = title
        self._fig, axes = plt.subplots(num_row, num_col, **plot_dict)
        try:
            self._axes = axes.flat
        except:
            self._axes = [axes]
        self._i = -1

    def add_subplot(
        self, title: str, xlabel: str = "", ylabel: str = "", plot_num: int = None
    ):
        if plot_num:
            self._i = plot_num
        else:
            self._i += 1
        ax = self._axes[self._i]

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        return ax

    def set_axes(self, plot_num: int = 0, **axesDict):
        ax = self._axes[plot_num]
        ax.set(**axesDict)
        return ax

    def add_line(self, ax, xdata, ydata, **style_dict):
        # if styleDict:
        # pv(styleDict)
        # ax.plot(xData, yData, **styleDict)
        # else:
        # ax.plot(xData, yData)
        ax.plot(xdata, ydata, **style_dict)

    def draw(self, is_legend=True):
        # plt.suptitle(self._title)
        plt.subplots_adjust(hspace=0.5, wspace=0.5)
        if is_legend:
            for ax in self._axes:
                ax.legend(loc="upper right")
        plt.show()


if __name__ == "__main__":

    import numpy as np

    np.seterr(divide="ignore", invalid="ignore")

    frm_root = tk.Tk()

    mat_plot_example = MatPlot(frm_root, r"Mesh Grid")
    # matPlot.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10), pady=(10, 10))
    mat_plot_example.pack(
        side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10), pady=(10, 10)
    )
    mat_plot_example.xdata = np.array(
        [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
    )

    y = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]])
    line_dict = {"label": "dashdot", "marker": ".", "markersize": 10, "linestyle": "-."}
    line_data = LineData(y, line_dict)
    mat_plot_example.add_line(line_data)
    mat_plot_example.draw()

    menubar = tk.Menu(frm_root)

    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="...", command=None)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=frm_root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    # toolMenu = tk.Menu(menubar, tearoff=False)

    # def show_sinH():
    # matPlot.show_line(0, showLineSinH.get())
    # matPlot.draw()

    # def show_sinL():
    # matPlot.show_line(1, showLineSinL.get())
    # matPlot.draw()

    # showLineSinH = tk.BooleanVar()
    # showLineSinH.set(True)
    # toolMenu.add_checkbutton(label="Show SinH", command=show_sinH, variable=showLineSinH)
    # showLineSinL = tk.BooleanVar()
    # showLineSinL.set(True)
    # toolMenu.add_checkbutton(label="Show SinL", command=show_sinL, variable=showLineSinL)

    # menubar.add_cascade(label="Tool", menu=toolMenu)

    frm_root.config(menu=menubar)

    frm_root.mainloop()
