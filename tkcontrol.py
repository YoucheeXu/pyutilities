# !/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import Any, override
import tkinter as tk

try:
    from winbasic import Control
except ImportError:
    from pyutilities.winbasic import Control


class tkControl(Control):
    def __init__(self, parent: tk.Misc, title: str, idself: str, tkctrl: tk.Widget):
        super().__init__(title, idself)
        self._parent: tk.Misc = parent
        self._tkctrl: tk.Widget = tkctrl
        self._assemble_type: str = ""

    @property
    def control(self):
        return self._tkctrl

    @property
    def visible(self):
        return self._tkctrl.winfo_viewable()

    @override
    def configure(self, **kwargs: Any):
        self._tkctrl.configure(**kwargs)

    """
    def grid(self, **options: Any):
            # cnf: Mapping[str, Any] | None = {},
            # *,
            # column: int = ...,
            # columnspan: int = ...,
            # row: int = ...,
            # rowspan: int = ...,
            # ipadx: _ScreenUnits = ...,
            # ipady: _ScreenUnits = ...,
            # padx: _ScreenUnits | tuple[_ScreenUnits, _ScreenUnits] = ...,
            # pady: _ScreenUnits | tuple[_ScreenUnits, _ScreenUnits] = ...,
            # sticky: str = ...,
            # in_: Misc = ...,
            # **kw: Any
        self._tkctrl.grid(**options)
        self._assemble_type = "grid"

    def pack(self, **options: Any):
        self._tkctrl.pack(**options)
        self._assemble_type = "pack"

    def place(self, **options: Any):
        self._tkctrl.place(**options)
        self._assemble_type = "place"

    def bind(self, *args: Any, **kwargs: Any):
        self._tkctrl.bind(*args, **kwargs)
    """

    # def bind(self, sequence: str, func: Callable[[tk.Event[tk.Widget]], object],
            # add: bool | Literal['', '+'] | None = None):
        # _ = self._tkctrl.bind(sequence, func, add)

    @override
    def __getitem__(self, item: str):
        # return getattr(self._tkctrl, item)
        return self._tkctrl[item]

    @override
    def __setitem__(self, item: str, value):
        self._tkctrl.__setitem__(item, value)

    @override
    def disable(self, is_disbl: bool = True):
        if is_disbl:
            self._tkctrl.configure(state="disabled")
        else:
            self._tkctrl.configure(state="normal")

    def _get_layout_method(self, widget: tk.Widget):
        """判断控件使用的布局方式（pack/grid/place）"""
        # 检查是否使用了 place
        try:
            if widget.tk.call("place", "info", widget):
                return "place"
        except tk.TclError as e:
            print(e)
        try:
            # 检查是否使用了 pack
            if widget.tk.call("pack", "info", widget):
                return "pack"
        except tk.TclError as e:
            print(e)
        try:
            # 检查是否使用了 grid
            if widget.tk.call("grid", "info", widget):
                return "grid"
        except tk.TclError as e:
            print(e)

        raise ValueError("未使用任何布局管理器")

    @override
    def hide(self, is_hide: bool = True):
        if not self._assemble_type:
            self._assemble_type = self._get_layout_method(self._tkctrl)
        match self._assemble_type:
            case "grid":
                if is_hide:
                    self._tkctrl.grid_remove()
                else:
                    self._tkctrl.grid()
            case "pack":
                if is_hide:
                    self._tkctrl.pack_forget()
                else:
                    self._tkctrl.pack()
            case "place":
                if is_hide:
                    self._tkctrl.place_forget()
                else:
                    self._tkctrl.place()
            case _:
                raise ValueError(f"unkown layout: {self._assemble_type}")

    @override
    def destroy(self):
        self._tkctrl.destroy()
