# !/usr/bin/python3
# -*- coding: UTF-8 -*-
from dataclasses import dataclass, field
import tkinter as tk
from typing import cast, Any

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.axes._axes import Axes
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numpy.typing import ArrayLike
import numpy as np

try:
    from logit import pv
    from tkcontrol import tkControl
except ImportError:
    from pyutilities.logit import pv
    from pyutilities.tkcontrol import tkControl


__version__ = "2.3.0"


font = {'family' : 'SimHei',
        'weight' : 'bold',
        'size'   : '16'}
plt.rc('font', **font)               # 步骤一（设置字体的更多属性）
plt.rc('axes', unicode_minus=False)  # 步骤二（解决坐标轴负数的负号显示问题）


@dataclass
class LineData:
    ydata: ArrayLike                                # np.ndarray / list
    style_dict: dict = field(default_factory=dict)
    visible: bool = True
    line: Line2D | None = None


class MatPlotCtrl(tkControl):
    def __init__(
        self,
        parent: tk.Widget,
        idself: str,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        size: tuple[float, float] = (640, 480),
    ):
        self._dpi: float = 100
        self._xdata: ArrayLike = []
        self._linedata_list: list[LineData] = []

        self._xmin: float = float("inf")
        self._xmax: float = float("-inf")
        self._ymin: float = float("inf")
        self._ymax: float = float("-inf")

        self._size: tuple[float, float] = cast(tuple[float, float], tuple(item / self._dpi for item in size))
        # print(f"size = {self._size}")
        fig: Figure = Figure(figsize=self._size, dpi=self._dpi)
        self._canvas: FigureCanvasTkAgg = FigureCanvasTkAgg(fig, parent)
        super().__init__(parent, title, idself, self._canvas.get_tk_widget())
        self._ax: Axes = fig.add_subplot()
        fig.subplots_adjust(bottom=0.25)
        self._create(title, xlabel, ylabel)

    def _create(self, title: str, xlabel: str, ylabel: str):
        _ = self._ax.set_title(title)
        _ = self._ax.set_xlabel(xlabel)
        _ = self._ax.set_ylabel(ylabel)
        self._ax.grid()
        # self._ax.legend(loc='upper right')
        self._ax.autoscale()

    """
    def pack(self, **pack_dict):
        self._canvas.get_tk_widget().pack(**pack_dict)
    """

    @property
    def xdata(self):
        return self._xdata

    @xdata.setter
    def xdata(self, xdata: ArrayLike):
        self._xdata = xdata

    def _plot(self, xdata: ArrayLike, ydata: ArrayLike, **style_dict: Any) -> Line2D:
        line = self._ax.plot(xdata, ydata, **style_dict)
        if isinstance(line, list):
            return line[0]
        else:
            return line

    def add_line(self, line_data: LineData):
        ydata = line_data.ydata
        if line_data.visible:
            line_data.line = self._plot(self._xdata, ydata,
                **line_data.style_dict)
            # pv(line_data.style_dict)
        # pv(type(line_data.line))
        self._linedata_list.append(line_data)

        return len(self._linedata_list) - 1

    def update_ydata(self, idx: int, ydata: ArrayLike):
        self._linedata_list[idx].ydata = ydata
        if self._linedata_list[idx].visible:
            cast(Line2D, self._linedata_list[idx].line).set_ydata(ydata)

    def show_line(self, idx: int, is_show: bool):
        line_data = self._linedata_list[idx]
        line_data.visible = is_show
        line = line_data.line
        pv(line)
        if is_show:
            if not line:
                line_data.line = self._plot(
                    self._xdata, line_data.ydata,
                    **line_data.style_dict
                )
        else:
            if line_data.line is not None:
                line_data.line.remove()
                del line_data.line
                # self._linedata_list[idx].line = None
                line_data.line = None
        # line_data.line.set_visible(is_show)
        # line_data.line.get_legend().set_visible(is_show)

    def _recalculate_axes_scale(self):
        self._ymin = float("inf")
        self._ymax = float("-inf")

        for line in self._linedata_list:
            if line.visible:
                ydata = line.ydata
                pv(type(ydata))
                try:
                    ymin = min(ydata)
                    ymax = max(ydata)
                except ValueError:
                    ymin = ydata.min()
                    ymax = ydata.max()

                self._ymin = min(self._ymin, ymin)
                self._ymax = max(self._ymax, ymax)

        self._ymin = -0.15 if self._ymin == 0 else self._ymin
        _ = self._ax.set_ylim(self._ymin * 1.05, self._ymax * 1.05)

        self._xmin = float("inf")
        self._xmax = float("-inf")

        try:
            xmin = min(self._xdata)
            xmax = max(self._xdata)
        except ValueError:
            xmin = self._xdata.min()
            xmax = self._xdata.max()
        # finally:
            # pass

        self._xmin = min(self._xmin, xmin)
        self._xmax = max(self._xmax, xmax)

        self._xmin = -0.15 if self._xmin == 0 else self._xmin
        _ = self._ax.set_xlim(self._xmin * 1.05, self._xmax * 1.05)

    def draw(self):
        self._recalculate_axes_scale()
        # for line_data in self._linedata_list:
            # if line_data.style_dict.get("label") is not None:
                # _ = self._ax.legend(loc="upper right")
        _, labels = self._ax.get_legend_handles_labels()
        if len(labels) >= 1:
            _ = self._ax.legend(loc="upper right")
        self._canvas.draw()


class Plot:
    def __init__(self, title: str = "", num_row: int = 1, num_col: int = 1, **plot_dict: Any):
        self._title: str = title
        fig, axs = plt.subplots(num_row, num_col, **plot_dict)
        self._fig: Figure = fig
        self._axes: list[Axes] = []
        try:
            self._axes = axs.flat
        except:
            self._axes = [axs]
        self._i: int = -1

    def add_subplot(self, title: str, xlabel: str = "",
            ylabel: str = "", plot_num: int | None = None):
        if plot_num is not None:
            self._i = plot_num
        else:
            self._i += 1
        ax = self._axes[self._i]

        _ = ax.set_xlabel(xlabel)
        _ = ax.set_ylabel(ylabel)
        _ = ax.set_title(title)

        return ax

    def set_axes(self, plot_num: int = 0, **axes_dict):
        ax = self._axes[plot_num]
        _ = ax.set(**axes_dict)
        return ax

    def add_line(self, ax: Axes, xdata: ArrayLike, ydata: ArrayLike, **style_dict):
        _, = ax.plot(xdata, ydata, **style_dict)

    def draw(self):
        # plt.suptitle(self._title)
        plt.subplots_adjust(hspace=0.5, wspace=0.5)

        for ax in self._axes:
            # pv(ax.get_legend())
            _, labels = ax.get_legend_handles_labels()
            if len(labels) >= 1:
                _ = ax.legend(loc="upper right")
        plt.show()


if __name__ == "__main__":

    import numpy as np

    # np.seterr(divide="ignore", invalid="ignore")

    root = tk.Tk()
    root.title("MatPlot Example")
    # 调整窗口大小并居中
    screen_width, screen_height = root.maxsize()    # 获取屏幕最大长宽
    w, h = 480, 240
    x = int((screen_width-w)/2)
    y = int((screen_height-h)/2)
    root.geometry(f'{w}x{h}+{x}+{y}')   # 设置窗口大小，调整位置
    # root.resizable(width=False, height=False)   # False表示不可以缩放，True表示可以缩放

    # plot_example = Plot("Mesh Grid")
    mat_plot_example = MatPlotCtrl(root, "Mesh Grid")
    mat_plot_example.pack(
        side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10), pady=(10, 10)
    )

    menubar = tk.Menu(root)

    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="...")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    _= root.config(menu=menubar)

    x = np.array(
        [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
    )
    mat_plot_example.xdata = x
    y = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]])
    line_dict = {"label": "haha", "marker": ".", "markersize": 10, "linestyle": "-."}
    linedata = LineData(y, line_dict)
    idx = mat_plot_example.add_line(linedata)
    mat_plot_example.draw()

    root.mainloop()
