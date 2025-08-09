# !/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import Any, override
import tkinter as tk

try:
    from logit import pv, pe, po
    from winbasic import Control
except ImportError:
    from pyutilities.logit import pv, pe, po
    from pyutilities.winbasic import Control


class tkControl(Control):
    def __init__(self, parent: tk.Widget, title: str, idself: str, tkctrl: tk.Widget):
        super().__init__(title, idself)
        self._parent: tk.Widget = parent
        self._tkctrl: tk.Widget = tkctrl
        self._assemble_type: str = "grid"

    @property
    def control(self):
        return self._tkctrl

    @property
    def visible(self):
        return self._tkctrl.winfo_viewable()

    @override
    def configure(self, **kwargs: Any):
        self._tkctrl.configure(**kwargs)

    def grid(self, **options: Any):
        """
            cnf: Mapping[str, Any] | None = {},
            *,
            column: int = ...,
            columnspan: int = ...,
            row: int = ...,
            rowspan: int = ...,
            ipadx: _ScreenUnits = ...,
            ipady: _ScreenUnits = ...,
            padx: _ScreenUnits | tuple[_ScreenUnits, _ScreenUnits] = ...,
            pady: _ScreenUnits | tuple[_ScreenUnits, _ScreenUnits] = ...,
            sticky: str = ...,
            in_: Misc = ...,
            **kw: Any
        """
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

    @override
    def hide(self, is_hide: bool = True):
        if self._assemble_type == "grid":
            if is_hide:
                self._tkctrl.grid_remove()
            else:
                self._tkctrl.grid()
        elif self._assemble_type == "pack":
            if is_hide:
                self._tkctrl.pack_forget()
            else:
                self._tkctrl.pack()
        elif self._assemble_type == "place":
            if is_hide:
                self._tkctrl.place_forget()
            else:
                self._tkctrl.place()            
        else:
            raise ValueError(f"no such assemble type: {self._assemble_type}")

    @override
    def destroy(self):
        self._tkctrl.destroy()
