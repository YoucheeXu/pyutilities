#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
import datetime
import calendar
import tkinter as tk
from tkinter import ttk
from typing import TypeAlias, Callable, Any


OnSelect: TypeAlias = Callable[[int], None]


class ScrollPicker(tk.Frame):
    def __init__(self, parent: tk.Tk | tk.Frame,
            cur: int, strt: int, end: int,
            on_select: OnSelect | None = None,
            **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._parent: tk.Tk | tk.Frame = parent

        self._bgn: int = strt
        self._end: int = end
        self._on_select: OnSelect | None = on_select
        self._selected_data: int = cur

        # 创建UI组件
        self._create_widgets()
        # 绑定鼠标事件
        self._bind_mouse_scroll()
        # 初始化预览内容
        self._update_previews()

        self._data_up2: tk.Label
        self._data_up1: tk.Label
        self._data_label: tk.Label
        self._data_down1: tk.Label
        self._data_down2: tk.Label

    @property
    def data(self):
        return self._selected_data

    def _create_widgets(self) -> None:
        # 配置网格权重，使布局更美观
        for i in range(5):  # 行
            _ = self.grid_rowconfigure(i, weight=1)
        for i in range(1):  # 列
            _ = self.grid_columnconfigure(i, weight=1)

        # 上方预览（+2）
        self._data_up2 = tk.Label(self, font=("SimHei", 10), fg="#888888", width=6,
            anchor="center")
        self._data_up2.grid(row=0, column=0)

        # 上方预览（+1）
        self._data_up1 = tk.Label(self, font=("SimHei", 12), fg="#555555", width=6,
            anchor="center")
        self._data_up1.grid(row=1, column=0)

        # 当前选中值
        self._data_label = tk.Label(
            self,
            text=str(self._selected_data),
            font=("SimHei", 16, "bold"),
            relief="solid",
            width=8,
            height=2,
            anchor="center",
            bg="white"
        )
        self._data_label.grid(row=2, column=0, padx=10)

        # 下方预览（-1）
        self._data_down1 = tk.Label(self, font=("SimHei", 12), fg="#555555", width=6,
            anchor="center")
        self._data_down1.grid(row=3, column=0)

        # 下方预览（-2）
        self._data_down2 = tk.Label(self, font=("SimHei", 10), fg="#888888", width=6,
            anchor="center")
        self._data_down2.grid(row=4, column=0)

    def _bind_mouse_scroll(self) -> None:  # 保护方法
        """ 绑定鼠标滚轮事件"""

        scrollable_data_widgets = [self._data_label, self._data_up1, self._data_up2,
            self._data_down1, self._data_down2]
        for widget in scrollable_data_widgets:
            _ = widget.bind("<MouseWheel>", self._on_data_scroll)
            _ = widget.bind("<Button-4>", self._on_data_scroll)
            _ = widget.bind("<Button-5>", self._on_data_scroll)

        # 鼠标悬停效果
        _ = self._data_label.bind("<Enter>", self._on_enter)
        _ = self._data_label.bind("<Leave>", self._on_leave)

    def _on_enter(self, event: tk.Event[tk.Label]) -> None:  # 保护方法
        """ 鼠标进入时的样式变化"""
        if hasattr(event.widget, 'config'):
            _ = event.widget.config(bg="#e0f0ff")

    def _on_leave(self, event: tk.Event[tk.Label]) -> None:  # 保护方法
        """ 鼠标离开时的样式恢复"""
        if hasattr(event.widget, 'config'):
            _ = event.widget.config(bg="white")

    def _update_previews(self) -> None:  # 保护方法
        """ 更新上下预览内容"""
        # 上方预览（+1和+2，受限于上限）
        up1 = self._selected_data + 1 if self._selected_data + 1 <= self._end else self._bgn
        up2 = self._selected_data + 2 if self._selected_data + 2 <= self._end else (self._selected_data + 2 - self._end)

        # 下方预览（-1和-2，受限于下限）
        down1 = self._selected_data - 1 if self._selected_data - 1 >= self._bgn else self._end
        down2 = self._selected_data - 2 if self._selected_data - 2 >= self._bgn else (self._selected_data - 2 + self._end)

        _ = self._data_up2.config(text=str(up2))
        _ = self._data_up1.config(text=str(up1))
        _ = self._data_down1.config(text=str(down1))
        _ = self._data_down2.config(text=str(down2))

    def _on_data_scroll(self, event: tk.Event) -> None:  # 保护方法
        """ 处理滚动"""
        if event.delta > 0 or getattr(event, 'num', 0) == 4:  # 上滚增加
            self._selected_data = self._selected_data + 1 if self._selected_data < self._end else self._bgn
        else:  # 下滚减少
            self._selected_data = self._selected_data - 1 if self._selected_data > self._bgn else self._end

        _ = self._data_label.config(text=str(self._selected_data))

        self._update_previews()

        if self._on_select is not None:
            self._on_select(self._selected_data)

    def update_data(self, data: int):
        self._selected_data = data
        self._update_previews()

    def set_max_data(self, maxdata: int):
        self._end = maxdata


class DateScrollPickerCtrl:
    def __init__(self, point: tuple[int, int] | None = None, title: str = ""):
        self._master: tk.Toplevel = tk.Toplevel()
        self._master.withdraw()

        self._frame: tk.Frame = tk.Frame(self._master)

        self._title: str = title if title else "日期选择器"

        # 初始日期设置
        today: datetime.datetime = datetime.datetime.today()
        self._selected_year: int = today.year
        self._selected_month: int = today.month
        self._selected_day: int = today.day

        self._year_scrollpicker: ScrollPicker = ScrollPicker(self._frame, self._selected_year,
            1970, 2100, self._on_year_change)

        self._month_scrollpicker: ScrollPicker = ScrollPicker(self._frame, self._selected_month,
            1, 12, self._on_month_change)

        self._day_scrollpicker: ScrollPicker = ScrollPicker(self._frame, self._selected_day,
            1, 31, self._on_day_change)

        # 创建UI组件
        self._create_widgets()

        self._confirm_btn: ttk.Button
        self._result_var: tk.StringVar
        self._result_label: ttk.Label

        self._frame.pack(expand = 1, fill = 'both')

        self._master.overrideredirect(True)
        self._master.update_idletasks()
        width, height = self._master.winfo_reqwidth(), self._master.winfo_reqheight()
        self.height: int = height
        if point:
            x, y = point[0], point[1]
        else:
            x, y = (self._master.winfo_screenwidth() - width)/2, \
                (self._master.winfo_screenheight() - height)/2
        self._master.geometry(f"{width}x{height}+{x}+{y}") # 窗口位置居中
        _ = self._master.after(300, self._main_judge)
        self._master.attributes('-topmost', True)
        self._master.grab_set()        # ensure all input goes to our window
        self._master.deiconify()
        self._master.focus_set()
        self._master.wait_window()

    def _create_widgets(self) -> None:
        # 配置网格权重，使布局更美观
        for i in range(3):  # 行
            _ = self._frame.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 列
            _ = self._frame.grid_columnconfigure(i, weight=1)

        ttk.Label(self._frame, text=self._title, font=("SimHei", 12)).grid(row=0, column=0,
            columnspan=3, pady=5)

        self._year_scrollpicker.grid(row=1, column=0)
        self._month_scrollpicker.grid(row=1, column=1)
        self._day_scrollpicker.grid(row=1, column=2)

        # 确认按钮和结果显示
        self._confirm_btn = ttk.Button(self._frame, text="确认选择", command=self._confirm)
        self._confirm_btn.grid(row=2, column=0, columnspan=3, pady=10)

        self._result_var = tk.StringVar()
        self._result_var.set(f"当前选择: {self._selected_year}-{self._selected_month:02d}-{self._selected_day:02d}")
        self._result_label = ttk.Label(self._frame, textvariable=self._result_var, font=("SimHei", 12))
        self._result_label.grid(row=3, column=0, columnspan=3, pady=5)

    def _on_year_change(self, year: int):
        self._selected_year = year
        self._adjust_day_range()
        self._update_result_preview()

    def _on_month_change(self, month: int):
        self._selected_month = month
        self._adjust_day_range()
        self._update_result_preview()

    def _on_day_change(self, day: int):
        self._selected_day = day
        self._update_result_preview()

    def _get_max_day(self) -> int:
        """ 获取当月最大天数"""
        return calendar.monthrange(self._selected_year, self._selected_month)[1]

    def _adjust_day_range(self) -> None:
        """ 调整日期以适应当前年月"""
        max_day = self._get_max_day()
        if self._selected_day > max_day:
            self._selected_day = max_day
            self._day_scrollpicker.update_data(self._selected_day)
        self._day_scrollpicker.set_max_data(max_day)

    def _update_result_preview(self) -> None:
        """ 更新结果预览"""
        formatted_date: str = f"{self._selected_year}-{self._selected_month:02d}-{self._selected_day:02d}"
        self._result_var.set(f"当前选择: {formatted_date}")

    def _confirm(self) -> str:
        """ 显示并返回最终选择的日期"""
        formatted_date: str = f"{self._selected_year}-{self._selected_month:02d}-{self._selected_day:02d}"
        self._result_var.set(f"已选择: {formatted_date}")
        self._exit()
        return formatted_date

    def get_datestr(self) -> str:
        """ 获取当前选择的日期"""
        return f"{self._selected_year}-{self._selected_month}-{self._selected_day}"

    def _exit(self):
        self._master.grab_release()
        self._master.destroy()

    def _main_judge(self):
        """ 判断窗口是否在最顶层"""
        try:
            if self._master.focus_displayof() is None \
                or 'toplevel' not in str(self._master.focus_displayof()):
                self._exit()
            else:
                _ = self._master.after(10, self._main_judge)
        except:
            _ = self._master.after(10, self._main_judge)


class TimeScrollPickerCtrl:
    def __init__(self, point: tuple[int, int] | None = None, title: str = ""):
        self._master: tk.Toplevel = tk.Toplevel()
        self._master.withdraw()

        self._frame: tk.Frame = tk.Frame(self._master)

        self._title: str = title if title else "时间选择器"

        # 初始时间设置
        now: datetime.datetime = datetime.datetime.now()
        self._selected_hour: int = now.hour
        self._selected_minute: int = now.minute

        self._hour_scrollpicker: ScrollPicker = ScrollPicker(self._frame, self._selected_hour,
            0, 23, self._on_hour_change)

        self._minute_scrollpicker: ScrollPicker = ScrollPicker(self._frame, self._selected_minute,
            0, 59, self._on_minute_change)

        self._confirm_btn: ttk.Button
        self._result_var: tk.StringVar
        self._result_label: ttk.Label

        # 创建UI组件
        self._create_widgets()

        self._frame.pack(expand = 1, fill = 'both')

        self._master.overrideredirect(True)
        self._master.update_idletasks()
        width, height = self._master.winfo_reqwidth(), self._master.winfo_reqheight()
        self.height: int = height
        if point:
            x, y = point[0], point[1]
        else:
            x, y = (self._master.winfo_screenwidth() - width)/2, \
                (self._master.winfo_screenheight() - height)/2
        self._master.geometry(f"{width}x{height}+{x}+{y}") # 窗口位置居中
        _ = self._master.after(300, self._main_judge)
        self._master.attributes('-topmost', True)
        self._master.grab_set()        # ensure all input goes to our window
        self._master.deiconify()
        self._master.focus_set()
        self._master.wait_window()

    def _create_widgets(self) -> None:
        # 配置网格权重，使布局更美观
        for i in range(3):  # 行
            _ = self._frame.grid_rowconfigure(i, weight=1)
        for i in range(2):  # 列
            _ = self._frame.grid_columnconfigure(i, weight=1)

        self._title_lbl = ttk.Label(self._frame, text=self._title, font=("SimHei", 12))
        self._title_lbl.grid(row=0, column=0, columnspan=3, pady=5)

        self._hour_scrollpicker.grid(row=1, column=1)
        self._minute_scrollpicker.grid(row=1, column=2)

        # 确认按钮和结果显示
        self._confirm_btn = ttk.Button(self._frame, text="确认选择", command=self._confirm)
        self._confirm_btn.grid(row=2, column=0, columnspan=3, pady=10)

        self._result_var = tk.StringVar()
        self._result_var.set(f"当前选择: {self._selected_hour:02d}:{self._selected_minute:02d}")
        self._result_label = ttk.Label(self._frame, textvariable=self._result_var, font=("SimHei", 12))
        self._result_label.grid(row=3, column=0, columnspan=3, pady=5)

    def _on_hour_change(self, hour: int):
        self._selected_hour = hour
        self._update_result_preview()

    def _on_minute_change(self, minute: int):
        self._selected_minute = minute
        self._update_result_preview()

    def _update_result_preview(self) -> None:
        """ 更新结果预览"""
        formatted_time: str = f"{self._selected_hour:02d}:{self._selected_minute:02d}"
        self._result_var.set(f"当前选择: {formatted_time}")

    def _confirm(self) -> str:
        """ 显示并返回最终选择的日期"""
        formatted_time: str = f"{self._selected_hour:02d}:{self._selected_minute:02d}"
        self._result_var.set(f"已选择: {formatted_time}")
        self._exit()
        return formatted_time

    def get_datestr(self) -> str:
        """ 获取当前选择的时间"""
        return f"{self._selected_hour:02d}:{self._selected_minute:02d}"

    def _exit(self):
        self._master.grab_release()
        self._master.destroy()

    def _main_judge(self):
        """ 判断窗口是否在最顶层"""
        try:
            if self._master.focus_displayof() is None \
                or 'toplevel' not in str(self._master.focus_displayof()):
                self._exit()
            else:
                _ = self._master.after(10, self._main_judge)
        except:
            _ = self._master.after(10, self._main_judge)


if __name__ == "__main__":
    class ScrollPickerCtrl_test():
        def __init__(self):

            self._root: tk.Tk = tk.Tk()

            # 设置tk窗口在屏幕中心显示
            sw = self._root.winfo_screenwidth()    # 得到屏幕宽度
            sh = self._root.winfo_screenheight()    # 得到屏幕高度
            ww = 300    # 设置窗口 宽度
            wh = 120    # 设置窗口 高度

            x = (sw - ww) / 2
            y = (sh - wh) / 2
            self._root.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

            self._frame: tk.Frame = tk.Frame(self._root)
            self._frame.pack()

            self._label_date: tk.Label = tk.Label(self._frame, width=10,
                text="选择日期", font="宋体, 12", justify='center')
            self._label_date.grid(row=0, column=0, padx=5, pady=5)

            self._var_date: tk.StringVar = tk.StringVar()
            self._entry_date: tk.Entry = tk.Entry(self._frame, width=10,
                textvariable=self._var_date, font="宋体, 12",
                                         justify='center', )
            self._entry_date.grid(row=0, column=1, padx=5, pady=5)

            self._button_seldate: tk.Button = tk.Button(self._frame, width=2,
                text='*', font="宋体, 12",
                justify='center',
                command=lambda: self.get_date(self._entry_date.winfo_rootx(),
                                    self._entry_date.winfo_rooty() + 20))
            self._button_seldate.grid(row=0, column=2, padx=5, pady=5)

            self._label_time: tk.Label = tk.Label(self._frame, width=10,
                text="选择时间", font="宋体, 12", justify='center')
            self._label_time.grid(row=1, column=0, padx=5, pady=5)

            self._var_time: tk.StringVar = tk.StringVar()
            self._entry_time: tk.Entry = tk.Entry(self._frame, width=10,
                textvariable=self._var_time, font="宋体, 12",
                                         justify='center', )
            self._entry_time.grid(row=1, column=1, padx=5, pady=5)

            self._button_seltime: tk.Button = tk.Button(self._frame, width=2,
                text='*', font="宋体, 12",
                justify='center',
                command=lambda: self.get_time(self._entry_time.winfo_rootx(),
                                    self._entry_time.winfo_rooty() + 20))
            self._button_seltime.grid(row=1, column=2, padx=5, pady=5)

            self._root.mainloop()

        def get_date(self, x: int, y: int):    # x, y位Entry的坐标位置
            # 接收弹窗的数据
            res = self.ask_date(x, y)
            if res is None:
                return
            self._var_date.set(res)

        def ask_date(self, x: int, y: int):
            scrollpicker = DateScrollPickerCtrl((x, y))
            return scrollpicker.get_datestr()

        def get_time(self, x: int, y: int):    # x, y位Entry的坐标位置
            # 接收弹窗的数据
            res = self.ask_time(x, y)
            if res is None:
                return
            self._var_time.set(res)

        def ask_time(self, x: int, y: int):
            scrollpicker = TimeScrollPickerCtrl((x, y), "wahaha")
            return scrollpicker.get_datestr()


    app = ScrollPickerCtrl_test()
