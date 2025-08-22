# !/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
# from _typeshed import SupportsWrite
import sys
import os
import platform
import ctypes
from functools import partial
# from collections import OrderedDict
from typing import Literal, Any, override, cast, Unpack
from typing import Protocol, TypeVar, Generic
# from typing import get_args, get_origin
# from collections.abc import Callable

import tkinter as tk
import tkinter.messagebox as tkMessageBox
from tkinter import ttk
from tkinter import scrolledtext
import xml.etree.ElementTree as et
from ast import literal_eval

import cv2
from PIL import Image, ImageTk    # for imgButton
# import PIL

from idlelib.statusbar import MultiStatusBar
from idlelib.tooltip import Hovertip

try:
    from logit import pv, pe, po
    from winbasic import EventHanlder, Widget, Dialog, WinBasic
    from tkcontrol import tkControl
    from matplot import MatPlotCtrl
    import cv2_utilities as cv2u
except ImportError:
    from pyutilities.logit import pv, pe, po
    from pyutilities.winbasic import EventHanlder, Widget, Dialog, WinBasic
    from pyutilities.tkcontrol import tkControl
    from pyutilities.matplot import MatPlotCtrl
    import pyutilities.cv2_utilities as cv2u


__version__ = "4.4.0"
IS_WINDOWS = platform.system() == "Windows"


class LabelCtrl(tkControl):
    def __init__(self, parent: tk.Misc, owner: Dialog, idself: str,
            text: str, clickable: bool, **options: Any):
        ctrl = ttk.Label(parent, text=text, **options)
        super().__init__(parent, text, idself, ctrl)
        if clickable:
            _= ctrl.bind("<Button-1>",
                lambda e: owner.process_message(idself,
                    mousepos=e.widget.winfo_pointerxy()))

    def get_text(self):
        lblctrl = cast(ttk.Label, self._tkctrl)
        return cast(str, lblctrl["text"])

    def set_text(self, val: str):
        lblctrl = cast(ttk.Label, self._tkctrl)
        lblctrl["text"] = val


class EntryCtrl(tkControl):
    def __init__(self, parent: tk.Misc, **options: Any):
        ctrl = ttk.Entry(parent)
        super().__init__(parent, "", "", ctrl)
        self._var: tk.StringVar = tk.StringVar()
        _= ctrl.configure(textvariable=self._var, **options)

    def get_val(self) -> str:
        return self._var.get()

    def set_val(self, val: str):
        self._var.set(val)


class ImagePanelCtrl(tkControl):
    def __init__(self, parent: tk.Misc, idself: str, imagefile: str, *,
            width: int = 0, height: int = 0, **options: Any):
        ctrl = tk.Label(parent)
        super().__init__(parent, "", idself, ctrl)
        self._image: ImageTk.PhotoImage | None = None
        if imagefile:
            image = self._read_image(imagefile, width, height)
            _ = ctrl.configure(text="", image=image, anchor=tk.CENTER, **options)
            self._image = image
        else:
            _ = ctrl.configure(text="", anchor=tk.CENTER, **options)

    def _read_image(self, imagepath: str, w: int, h: int):
        image = cv2u.read_image(imagepath)
        if w:
            # pv(w)
            # pv(h)
            image = cv2u.scale_image(image, w, h)
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # convert the images to PIL format...
        image2 = Image.fromarray(image)
        # ...and then to ImageTk format
        image3 = ImageTk.PhotoImage(image2)
        return image3

    def display_image(self, image: cv2.typing.MatLike):
        # OpenCV represents images in BGR order however PIL represents
        # images in RGB order, so we need to swap the channels
        image1 = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # convert the images to PIL format...
        image2 = Image.fromarray(image1)

        # ...and then to ImageTk format
        image3 = ImageTk.PhotoImage(image2)

        _ = cast(tk.Label, super().control).configure(image=image3)
        self._image = image3


class ButtonCtrl(tkControl):
    def __init__(self, parent: tk.Misc, owner: Dialog, idself: str, text: str,
            **options: Any):
        ctrl = ttk.Button(parent, text=text, **options)
        tkControl.__init__(self, parent, text, idself, ctrl)
        self._owner: Dialog = owner
        _ = ctrl.configure(command=self._btn_clicked, **options)

    def _btn_clicked(self):
        btn = cast(ttk.Button, self._tkctrl)
        _ = self._owner.process_message(self._idself,
            mousepos=(btn.winfo_rootx(), btn.winfo_rooty()))


class ImageBtttonCtrl(tkControl):
    def __init__(self, parent: tk.Misc, owner: Dialog, idself: str, *,
            respath: str, imagefile: str, text: str | None,
            width: int = 0, height: int = 0,
            **options: Any):
        ctrl = tk.Button(parent, **options)
        title = text if text else ""
        tkControl.__init__(self, parent, title, idself, ctrl)
        self._res_path: str = respath
        self._ww: int = width
        self._image: ImageTk.PhotoImage
        self._hh: int = height if height else width if width else 0

        imagefile = os.path.join(self._res_path, imagefile)
        eimg = self._read_image(imagefile, self._ww, self._hh)
        # if eimg is None:
            # raise RuntimeError(f"fail to read image: {imagefile}")

        def cmd():
            _ = owner.process_message(idself,
                mousepos=(ctrl.winfo_rootx(), ctrl.winfo_rooty()))

        if text is not None:
            _ = ctrl.configure(text=text, image=eimg, command=cmd, compound=tk.LEFT,
                relief=tk.FLAT, **options)
                # **options)
        else:
            _ = ctrl.configure(image=eimg, command=cmd, relief=tk.FLAT, **options)
        self._image = eimg

    def _read_image(self, imagepath: str, w: int, h: int):
        # image = cv2.imread(imagepath, cv2.IMREAD_UNCHANGED)
        image = cv2u.read_image(imagepath)
        if w:
            # image = cv2.resize(image, (w, h), interpolation=cv2.INTER_CUBIC)
            image = cv2u.scale_image(image, w, h, cv2.INTER_CUBIC)
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # convert the images to PIL format...
        image2 = Image.fromarray(image)
        # ...and then to ImageTk format
        image3 = ImageTk.PhotoImage(image2)
        return image3

    # TODO: wait to test
    def change_image(self, imagefile: str, w: int = 0, h: int = 0):
        imagefile = os.path.join(self._res_path, imagefile)
        if not w:
            w, h = self._ww, self._hh
        photo = self._read_image(imagefile, w, h)
        # if photo is not None:
        btn = cast(tk.Button, super().control)
        _ = btn.configure(image=photo)
        # btn.image = photo
        self._image = photo


class CheckButtonCtrl(tkControl):
    def __init__(self, parent: tk.Misc, owner: Dialog, idself: str, *,
            text: str, vartext: str, select: bool, **options: Any):
        ctrl = tk.Checkbutton(parent)
        tkControl.__init__(self, parent, "", idself, ctrl)
        self._vartext: str = "_" + vartext
        self.__dict__[self._vartext] = tk.IntVar()
        variable = cast(tk.IntVar, self.__dict__[self._vartext])
        _ = ctrl.configure(text=text,
            variable=variable, **options)
        _ = variable.trace_add("write",
            lambda u0, u1, u2: owner.process_message(vartext, event="Changed",
                val=variable.get()))

        if select:
            ctrl.select()

    def get_val(self) -> int:
        return cast(tk.IntVar, self.__dict__[self._vartext]).get()


class ComboboxCtrl(tkControl):
    def __init__(self, parent: tk.Misc, owner: Dialog, *,
            idself: str, default: int, **options: Any):
        ctrl = ttk.Combobox(parent)
        super().__init__(parent, "", idself, ctrl)
        self._var: tk.StringVar = tk.StringVar()
        _ = ctrl.configure(textvariable=self._var, **options)
        _ = ctrl.current(default)
        _ = ctrl.bind(
            "<<ComboboxSelected>>",
            lambda event: owner.process_message(
                idself, event="Selected", val=self._var.get()
            ),
        )

    def get_val(self) -> str:
        return self._var.get()

    def set_val(self, val: str):
        self._var.set(val)

    def select(self, idx: int):
        ctrl = cast(ttk.Combobox, self._tkctrl)
        return ctrl.current(idx)


class ListboxCtrl(tkControl):
    def __init__(self, parent: tk.Misc, idself: str,
            **options: Any):
        ctrl = tk.Listbox(parent)
        tkControl.__init__(self, parent, "", idself, ctrl)

    def insert(self, index: str | int, *elements: str | float):
        ctrl = cast(tk.Listbox, self._tkctrl)
        ctrl.insert(index, *elements)
        # self.scroll_to_bottom_if_needed()

    def scroll_to_bottom_if_needed(self):
        ctrl  = cast(tk.Listbox, self._tkctrl)
        # 获取滚动条位置
        scrollbar_position = ctrl.yview()[1]
        # 检查滚动条是否在最底部
        if scrollbar_position != 1.0:
            # 在最底部时，执行自动滚动
            ctrl.see(tk.END)


class RadioButtonCtrl(tkControl):
    def __init__(self, parent: tk.Misc, owner: Dialog, idself: str, *,
            text: str, vartext: str, value: int, **options: Any):
        ctrl = ttk.Radiobutton(parent)
        tkControl.__init__(self, parent, "", idself, ctrl)
        # self._app: GuiBasic = app
        self._master: Dialog = owner
        self._vartext: str = vartext
        if self._vartext not in self._master.__dict__:
            self._master.__dict__[self._vartext] = tk.IntVar()
        variable = cast(tk.IntVar, self._master.__dict__[self._vartext])
        _ = ctrl.configure(text=text,
            variable=variable, value=value,
            command=lambda: owner.process_message(vartext, event="Changed", val=variable.get()),
            **options)

    def get_val(self) -> int:
        # return self.__dict__[self._vartext].get()
        return cast(tk.IntVar, self._master.__dict__[self._vartext]).get()


class RadioButtonGroupCtrl(tkControl):
    def __init__(self, parent: tk.Misc, app: WinBasic, owner: Dialog, idself: str, *,
            text: str, subctrlcfg: et.Element,
            level: int, **options: Any):
        ctrl = ttk.LabelFrame(parent)
        super().__init__(parent, text, idself, ctrl)
        # self._idself: str = idself
        # self._var_val: tk.IntVar = tk.IntVar()
        self._vartext: str = "_var" + text.replace(" ", "_")
        self._app: WinBasic = app
        self._owner: Dialog = owner
        # pv(options)
        _ = self.configure(text=text, **options)
        # self._radbutton_lst: list[ttk.Radiobutton] = []
        self._radbutton_lst: list[RadioButtonCtrl] = []
        _ = self._create_subctrls(subctrlcfg, level)

    def get_val(self) -> int:
        # return self._var_val.get()
        return cast(tk.IntVar, self._app.__dict__[self._vartext]).get()

    def set_val(self, val: int):
        # self._var_val.set(val)
        cast(tk.IntVar, self._app.__dict__[self._vartext]).set(val)

    def _create_subctrls(self, subctrls: et.Element, level: int):
        for subctrl_cfg in subctrls:
            radbtn_attr_dict = subctrl_cfg.attrib
            value = int(radbtn_attr_dict["value"])
            text: str = radbtn_attr_dict["text"]
            sub_ctrl = self._add_radiobutton(value, text)
            # self._app.debug_print(f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
            self._app.assemble_control(sub_ctrl, radbtn_attr_dict)

    def _add_radiobutton(self, val: int, txt: str, **opt_dict: Any):
        # radbutton = ttk.Radiobutton(self._parent, variable=self._var_val, **opt_dict)
        radbutton = RadioButtonCtrl(super().control, self._owner, "",
            text=txt, vartext=self._vartext, value=val, **opt_dict)
        self._radbutton_lst.append(radbutton)
        return radbutton

    @override
    def destroy(self):
        po(f"RadiobuttonGroupCtrl {self._idself} destroy")
        for radbutton in self._radbutton_lst:
            # self._debug_print(f"going to del {id_ctrl}")
            radbutton.destroy()
        self._radbutton_lst.clear()
        super().destroy()


class NotebookCtrl(tkControl):
    def __init__(self, parent: tk.Misc, app: WinBasic, idself: str, *,
            subctrlcfg_list: list[et.Element], level: int, **options: Any):
        ctrl = ttk.Notebook(parent, **options)
        tkControl.__init__(self, parent, "", idself, ctrl)
        # app.debug_print()
        self._app: WinBasic = app
        self._idself: str = idself
        self._idctrl_list: list[str] = []
        for subctrl_cfg in list(subctrlcfg_list):
            id_, sub_ctrl = self._app.create_control(self,
                subctrl_cfg, level + 1)
            self._idctrl_list.append(id_)
            # app.debug_print(f"tabCtrl: {subctrl_cfg.tag}")
            subctrl = cast(tk.Widget, cast(tkControl, sub_ctrl).control)
            ctrl.add(subctrl, text=subctrl_cfg.attrib["text"])
            for item in list(subctrl_cfg):
                idctrl_list = self._app.create_controls(sub_ctrl, item,
                    level + 2)
                self._idctrl_list.extend(idctrl_list)

    @override
    def destroy(self):
        po(f"NotebookCtrl {self._idself} destroy")
        for idctrl in self._idctrl_list:
            self._app.delete_control(idctrl)
        self._idctrl_list.clear()
        super().destroy()


# TODO: not fininsed
class FrameCtrl(tkControl):
    def __init__(self, parent: tk.Misc, idself: str, **options):
        ctrl = tk.Frame(parent, **options)
        tkControl.__init__(self, parent, "", idself, ctrl)

    @override
    def destroy(self):
        po(f"FrameCtrl {self._idself} destroy")
        super().destroy()


# TODO: not fininsed
class LabelFrameCtrl(tkControl):
    def __init__(self, parent: tk.Misc, title:str, idself: str, **options):
        ctrl = ttk.LabelFrame(parent, text=title, **options)
        tkControl.__init__(self, parent, title, idself, ctrl)

    @override
    def destroy(self):
        po(f"LabelFrameCtrl {self._idself} destroy")
        super().destroy()


class ScrollableFrameCtrl(tkControl):
    """ 智能滚动容器
    """
    def __init__(self, parent: tk.Misc, app: WinBasic, idself: str,
            width: int = 0, height: int = 0, **options: Any):
        self._outter_frame: tk.Frame = tk.Frame(parent, **options)

        # 配置网格布局权重，确保框架能扩展
        _ = self._outter_frame.grid_rowconfigure(0, weight=1)
        _ = self._outter_frame.grid_columnconfigure(0, weight=1)

        self._os_type: str = platform.system()
        self._update_after_id: str | None = None

        # 创建画布
        self._canvas: tk.Canvas = tk.Canvas(self._outter_frame, width=width, height=height,
            highlightthickness=0, highlightbackground="#ccc", takefocus=True)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # 垂直滚动条
        self._vscrollbar: ttk.Scrollbar = ttk.Scrollbar(self._outter_frame, orient="vertical",
            command=self._canvas.yview)
        self._vscrollbar.grid(row=0, column=1, sticky="ns")
        self._vscrollbar.grid_remove()  # 默认隐藏
        _ = self._canvas.configure(yscrollcommand=self._vscrollbar.set)

        # 水平滚动条
        self._hscrollbar: ttk.Scrollbar = ttk.Scrollbar(self._outter_frame, orient="horizontal",
            command=self._canvas.xview)
        _ = self._hscrollbar.grid(row=1, column=0, sticky="ew")
        self._hscrollbar.grid_remove()  # 默认隐藏
        _ = self._canvas.configure(xscrollcommand=self._hscrollbar.set)

        # Create a frame inside the canvas which will be scrolled with it
        self._inner_frame: tk.Frame = tk.Frame(self._canvas)
        super().__init__(parent, "", idself, self._inner_frame)

        # self._outter_frame.bindtags((self._outter_frame, self._canvas, "Frame", "all"))
        # 调整bindtags，确保事件先传给自身，再传给画布
        # self._inner_frame.bindtags((self._inner_frame, self._canvas, "Frame", "all"))

        self._interior_id: int = self._canvas.create_window((0, 0),
            window=self._inner_frame, anchor="nw")

        # 绑定事件处理
        _ = self._inner_frame.bind('<Configure>', self._on_configure_inner)
        _ = self._canvas.bind('<Configure>', self._on_configure_canvas)
        _ = self._inner_frame.bind("<Map>", self._on_map_inner)

        # 鼠标滚轮支持
        self._bind_scroll_events(self._canvas)
        self._bind_scroll_events(self._inner_frame)
        # self._bind_scroll_events(self._outter_frame)

        # 初始更新
        self._outter_frame.update_idletasks()
        self._on_configure_inner(None)

    def _bind_scroll_events(self, widget: tk.Widget):
        """为单个控件绑定所有必要的滚动事件"""
        if self._os_type == "Linux":
            vevents = ["<Button-4>",            # 上滚
                "<Button-5>"]                   # 下滚
            hevents = ["<Shift-Button-4>",      # 左滚
                "<Shift-Button-5>"]             # 右滚
        else:
            vevents = ["<MouseWheel>"]          # 垂直滚动
            hevents = ["<Shift-MouseWheel>"]    # 水平滚动
            if self._os_type == "Darwin":
                hevents.append("<Command-MouseWheel>")

        # 为控件绑定滚动事件处理函数
        for event in vevents:
            _ = widget.bind(event, self._on_vmousewheel)
        for event in hevents:
            _ = widget.bind(event, self._on_hmousewheel)

    def update_layout(self) -> None:
        """公共方法：更新布局和滚动区域"""
        self._on_configure_inner(None)

    def _on_map_inner(self, event: tk.Event[tk.Frame]) -> None:
        """当内部控件被映射时强制更新布局"""
        self._outter_frame.update_idletasks()
        self._on_configure_inner(event)

    def _on_configure_inner(self, event: tk.Event[tk.Frame] | None):
        """内容变化时更新滚动区域"""

        self._outter_frame.update_idletasks()

        # Update the scrollbars to match the size of the inner frame
        width = self._inner_frame.winfo_reqwidth()
        height = self._inner_frame.winfo_reqheight()
        _ = self._canvas.config(scrollregion=(0, 0, width, height))

        # if self._inner_frame.winfo_reqwidth() != self._canvas.winfo_width():
            # Update the canvas's width to fit the inner frame
            # _ = self._canvas.config(width=self._inner_frame.winfo_reqwidth())

        # 垂直滚动条显示逻辑
        canvas_height = self._canvas.winfo_height()
        if height > canvas_height + 5:
            _ = self._vscrollbar.grid()
        else:
            self._vscrollbar.grid_remove()

        # 水平滚动条显示逻辑
        canvas_width = self._canvas.winfo_width()
        if width > canvas_width + 5:
            _ = self._hscrollbar.grid()
        else:
            self._hscrollbar.grid_remove()

        # 为所有子控件绑定滚动事件
        for widget in self._inner_frame.winfo_children():
            if not hasattr(widget, '_scroll_events_bound'):
                self._bind_scroll_events(widget)
                widget._scroll_events_bound = True  # 标记为已绑定

    def _on_configure_canvas(self, event: tk.Event[tk.Canvas]):
        """画布大小变化时调整"""
        if self._inner_frame.winfo_reqwidth() != self._canvas.winfo_width():
            # Update the inner frame's width to fill the canvas
            _ = self._canvas.itemconfigure(self._interior_id, width=self._canvas.winfo_width())
            # _ = self._canvas.itemconfig(self._interior_id, width=event.width)
        if self._update_after_id is not None:
            self._outter_frame.after_cancel(self._update_after_id)

        self._update_after_id = self._outter_frame.after(30, self._on_configure_inner, None)

    def _on_vmousewheel(self, event: tk.Event[tk.Misc]):
        """垂直滚动处理"""
        if not self._vscrollbar.winfo_viewable():
            return None
        # po("_on_vmousewheel")
        # if not self._vscrollbar.winfo_ismapped():
            # return "break"
        # delta = event.delta
        # pv(delta)
        # scroll_units = -1 if delta > 0 else 1
        delta = event.delta if hasattr(event, 'delta') else -1 if event.num == 4 else 1
        scroll_units = -int(delta / 120)
        self._canvas.focus_set()
        self._canvas.yview_scroll(scroll_units, "units")
        # 阻止事件传播到其他组件
        return "break"

    def _on_hmousewheel(self, event: tk.Event[tk.Misc]):
        """水平滚动处理"""
        if not self._hscrollbar.winfo_viewable():
            return None
        # po("_on_hmousewheel")
        # self.update_layout()

        # if not self._hscrollbar.winfo_ismapped():
            # return "break"

        _ = event.widget.focus_set()

        delta = event.delta if hasattr(event, 'delta') else -1 if event.num == 4 else 1
        scroll_units = -int(delta / 120)
        _ = self._canvas.xview_scroll(scroll_units, "units")
        # 阻止事件传播到其他组件
        return "break"

    @property
    def outter(self):
        return self._outter_frame

    @override
    def destroy(self):
        po(f"ScrollableFrame {self._idself} destroy")
        self._inner_frame.destroy()
        self._vscrollbar.destroy()
        self._hscrollbar.destroy()
        self._canvas.destroy()
        super().destroy()


# TODO: 1. Tip
class PicsListviewCtrl(tkControl):
    def __init__(self, parent: tk.Misc, app: WinBasic, owner: Dialog, idself: str,
            num_column: int, pic_size: int, res_path: str):
        ctrl = ttk.Frame(parent)
        tkControl.__init__(self, parent, "", idself, ctrl)
        self._image_group: list[ttk.LabelFrame] = []
        self._imagepanel_llist: list[list[ImagePanelCtrl]] = []
        self._app: WinBasic = app
        self._owner: Dialog = owner
        self._num_column: int = num_column
        self._pic_size: int = pic_size
        self._res_path: str = res_path
        self._grp_seld: int = 0
        self._idx_seld: int = 0
        self._idx_lstseld: list[int] = [0, 0]
        self._spacing: int = int(self._pic_size/10)
        self._groupidx: int = 0

    def add_imagegroup(self, title: str, imagefile_list: list[str]):
        frame = ttk.LabelFrame(self._tkctrl, text=title)
        imagepanel_list: list[ImagePanelCtrl] = []
        for i, imagefile in enumerate(imagefile_list):
            imagefile = os.path.join(self._res_path, imagefile)
            image_panel = ImagePanelCtrl(frame, "", imagefile,
                width=self._pic_size, height=self._pic_size)
            image_panel.control.grid(row=i // self._num_column, column=i % self._num_column,
                padx=self._spacing, pady=self._spacing)
            _= image_panel.control.bind("<Button-1>",
                lambda e, grp=self._groupidx, idx=i: self.select(grp, idx))
            imagepanel_list.append(image_panel)
        self._imagepanel_llist.append(imagepanel_list)
        frame.pack()
        self._image_group.append(frame)
        self._groupidx += 1

    def select(self, grp:int, idx: int):
        self._idx_lstseld = [self._grp_seld, self._idx_seld]
        self._grp_seld = grp
        self._idx_seld = idx

        old_imagepanle = self._imagepanel_llist[self._idx_lstseld[0]][self._idx_lstseld[1]]
        _ = old_imagepanle.configure(highlightthickness=0)
        imagepanel = self._imagepanel_llist[self._grp_seld][self._idx_seld]
        _ = imagepanel.configure(highlightbackground="blue", highlightthickness=2)
        _ = self._owner.process_message(self._idself, event="clicked",
            group=self._grp_seld, index=self._idx_seld)

    def get_selected(self) -> tuple[int, int]:
        return self._grp_seld, self._idx_seld

    @override
    def destroy(self):
        po(f"PicsListviewCtrl {self._idself} destroy")
        for group in self._imagepanel_llist:
            for image in group:
                image.destroy()
        self._imagepanel_llist.clear()
        for frm in self._image_group:
            frm.destroy()
        self._image_group.clear()
        self._tkctrl.destroy()
        self._grp_seld = 0
        self._idx_seld = 0
        super().destroy()


class ToolbarCtrl(tkControl):
    def __init__(self, parent: tk.Misc, app: WinBasic, res_path: str,
            subctrls: list[et.Element], **options):
        ctrl = ttk.Frame(parent, **options)
        tkControl.__init__(self, parent, "", "", ctrl)
        self._res_path: str = res_path
        self._app: WinBasic = app
        self._idctrl_list: list[str] = []
        for subctrl in subctrls:
            idctrl_list = self._app.create_controls(self, subctrl, 1)
            self._idctrl_list.extend(idctrl_list)

    @override
    def destroy(self):
        for idctrl in self._idctrl_list:
            self._app.delete_control(idctrl)
        self._idctrl_list.clear()
        super().destroy()


T = TypeVar("T", bound=tk.Tk | tk.Toplevel)
class tkWM(Generic[T], Widget):
    def __init__(self, wm: T):
        super().__init__()
        self._tkwm: T = wm

    @property
    def control(self):
        return self._tkwm


# TODO: auto scrollable or not
class DialogCtrl(Dialog):
    def __init__(self, parent: tk.Tk | tk.Toplevel, app: WinBasic, idself: str, *,
            title: str, width: int, height: int,
            subctrlcfg_list: list[et.Element], **options: Any):
        super().__init__(title, width, height)
        # self._parent: tk.Widget = parent
        self._parent: tk.Tk | tk.Toplevel = parent
        self._owner: Dialog | None = None
        # self._top: tk.Toplevel | None = None
        self._top: tkWM[tk.Toplevel] | None = None
        self._app: WinBasic = app
        self._alive: bool = False
        self._idself: str = idself
        self._subctrlcfg_list: list[et.Element] = subctrlcfg_list
        self._idctrl_list: list[str] = []
        self._extral_msg: dict[str, object] = {}

    @property
    def owner(self):
        if self._owner is not None:
            return self._owner
        else:
            return self._app

    @override
    def set_title(self, val: str):
        super().set_title(val)
        if self._top is not None:
            self._top.control.title(self._title)

    @property
    def alive(self):
        return self._alive

    def do_show(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: object):
        po(f"show Dialog {self._idself}: {kwargs}")
        # self.deiconify()
        self._alive = True
        if owner is not None:
            self._owner = owner

        self._top = tkWM[tk.Toplevel](tk.Toplevel(self._parent))

        # x, y, _, _ = self._app.get_winsize()
        if owner is not None:
            self._xx: int = x
            self._yy: int = y
        else:
            self._xx = self._parent.winfo_rootx() + x
            self._yy = self._parent.winfo_rooty() + y
        # pv(self.pos)

        self._top.control.geometry(f'{self._ww}x{self._hh}+{self._xx}+{self._yy}')

        # self.withdraw()
        iddlg = self._idself

        frmdlg_xml = self._app.create_xml("Top", {})

        id_frmain = f"frmMain{iddlg}"
        # frmain_xml = self._app.create_xml("Frame", {"id": id_frmain}, frmdlg_xml)
        frmain_xml = self._app.create_xml("ScrollableFrame", {"id": id_frmain,
            "Width": f"{self._ww-30}", "Height": f"{self._hh-160}"}, frmdlg_xml)
        _, frmmain_ctrl = self._app.create_control(self._top,
            frmain_xml, 0, self)
        # self._idctrl_list.append(id_frmain)
        self._idctrl_dict[id_frmain] = frmmain_ctrl
        # frm_main = cast(tkControl, frmmain).control
        # frm_main = cast(tkControl, frmmain_ctrl)

        for sub_ctrl in self._subctrlcfg_list:
            subidctrl_dict = self._app.create_controls(frmmain_ctrl, sub_ctrl, 1, self)
            # self._idctrl_list.extend(subidctrl_list)
            self._idctrl_dict.update(subidctrl_dict)

        _ = self._app.assemble_control(frmmain_ctrl, {"layout": "pack",
            "pack": "{'side':'top','fill':'both','expand':True,'padx':5,'pady':5}"})

        frmbot_xml = self._app.create_xml("Frame", {"id": f"frmBot{iddlg}"}, frmdlg_xml)
        id_frmbot, frmbot_ctrl = self._app.create_control(self._top,
            frmbot_xml, 0, self)
        # self._idctrl_list.append(id_frmbot)
        self._idctrl_dict[id_frmbot] = frmbot_ctrl

        btnConfirm_xml = self._app.create_xml("Button", {"id": f"btnConfirm{iddlg}",
            "text": "Confirm", "options": "{'width':20}"}, frmbot_xml)
        id_btnconfirm, btnConfirm_ctrl = self._app.create_control(frmbot_ctrl,
            btnConfirm_xml, 1, self)
        # self._idctrl_list.append(idctrl)
        self._idctrl_dict[id_btnconfirm] = btnConfirm_ctrl
        _ = self._app.assemble_control(btnConfirm_ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")

        bntcancel_xml = self._app.create_xml("Button", {"id": f"btnCancel{iddlg}",
            "text": "Cancel", "options": "{'width':20}"}, frmbot_xml)
        id_bntcancel, bntcancel_ctrl = self._app.create_control(frmbot_ctrl,
            bntcancel_xml, 1, self)
        # self._idctrl_list.append(idctrl)
        self._idctrl_dict[id_bntcancel] = bntcancel_ctrl
        # pv(self._idctrl_list)
        _ = self._app.assemble_control(bntcancel_ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")

        _ = self._app.assemble_control(frmbot_ctrl, {"layout": "pack",
            "pack": "{'side':'bottom','fill':'x','expand':True,'padx':5,'pady':5}"})

        self._extral_msg = kwargs
        _ = self.process_message("beforego", **kwargs)

        self._top.control.title(self._title)

        # Disable the window's resizing capability
        _ = self._top.control.resizable(width=tk.FALSE, height=tk.FALSE)
        # self._top.wait_visibility() # can't grab until window appears, so we wait
        self._top.control.transient(self._parent)   # dialog window is related to main
        self._top.control.protocol("WM_DELETE_WINDOW", self.destroy) # intercept close button

        Dialog.register_eventhandler(self, "btnCancel" + self._idself, self._do_cancel)
        # Dialog.register_eventhandler(self, "btnCancel" + self._idself,
            # lambda mousepos: self._do_cancel(**kwargs))
        Dialog.register_eventhandler(self, "btnConfirm" + self._idself, self._do_confirm)

        if self._owner is not None:
            self._owner.back()
        super().back(False)

        # 设置achieved_value，使该窗口始终处于其他窗口的上层
        _ = self._top.control.wm_attributes("-topmost", True)  # pyright: ignore[reportUnknownMemberType]
        self._top.control.grab_set()        # ensure all input goes to our window
        self._top.control.wm_deiconify()
        # self._parent.wait_window(self._top)
        self._top.control.wait_window()
        # pv(self._id_list)

    def get_control(self, idctrl: str) -> object:
        return self._app.get_control(idctrl)

    def _do_cancel(self, **kwargs: object):
        po(f"Dialog {self._idself} _do_cancel")
        self.destroy(confirm=False, **kwargs)

    def _do_confirm(self, **kwargs: object):
        po(f"Dialog {self._idself} _do_confirm")
        self.destroy(confirm=True, **kwargs)

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        kwargs.update(self._extral_msg)
        return super().process_message(idmsg, **kwargs)

    @override
    def destroy(self, **kwargs: object):
        po(f"Dialog {self._idself} destroy")
        # pv(kwargs)
        confirm = cast(bool, kwargs.get("confirm", False))
        if self._top:
            if confirm:
                ret, msg = cast(tuple[bool, str],
                    super().process_message("confirm", **kwargs))
                if not ret:
                    self._app.show_err(self._title, msg)
                    return
            else:
                _ = self.process_message("cancel", **kwargs)
            try:
                before_close = cast(EventHanlder, getattr(
                        self, "_before_close"
                    ))  # get before_close from child
                ret, msg = cast(tuple[bool, str],before_close(**kwargs))
                if not ret:
                    self._app.show_err(self._title, msg)
                    return
            except AttributeError as r:
                po(f"{self._title} Warnning to exit: {r}")

            self._top.control.grab_release()
            super().back()
            # for idctrl in self._idctrl_list:
            for idctrl, _ in self._idctrl_dict.items():
                self._app.delete_control(idctrl)
            # po("subctrl have been deleted!")
            # self._idctrl_list.clear()
            self._idctrl_dict.clear()
            self._top.control.destroy()
            self._top = None
        self._alive = False
        if self._owner is not None:
            self._owner.back(False)
        super().destroy()

_T_contra = TypeVar("_T_contra", contravariant=True)
class SupportsWrite(Protocol[_T_contra]):
    """自定义协议：表示支持 write(str) 方法的对象"""
    def write(self, s: str) -> object: ...


# class Root(tkControl):
    # def __init__(self):
        # self._win: tk.Tk = tk.Tk()
        # super().__init__(self._win, "", "", self._win)


class tkWin(WinBasic):
    def __init__(self, cur_path: str, xmlfile: str):
        super().__init__(xmlfile)
        self._is_debug: bool = False

        # Windows提前启用DPI感知
        if sys.platform.startswith("win"):
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        # self._win: tk.Tk = tk.Tk()
        self._root: tkWM[tk.Tk] = tkWM[tk.Tk](tk.Tk())
        self._win: tk.Tk = self._root.control

        """
        if IS_WINDOWS:
            try:  # >= win 8.1
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:  # win 8.0 or less
                ctypes.windll.user32.SetProcessDPIAware()
            # ctypes.windll.shcore.SetProcessDpiAwareness(1)
            scale_fact = cast(float, ctypes.windll.shcore.GetScaleFactorForDevice(0))
            pv(scale_fact)
            self._win.tk.call("tk", "scaling", scale_fact / 90)
        """
        self._scale_factor: float = self._get_scale_factor()
        self._win.tk.call("tk", "scaling", self._scale_factor)

        exit_window = partial(self.exit)
        self._win.protocol("WM_DELETE_WINDOW", exit_window)
        # 注册（绑定）窗口变动事件
        _ = self._win.bind('<Configure>', self._on_winresize)
        _ = self._win.bind_all("<KeyPress>", self._on_keypress)
        # _ = self._win.bind_all("<MouseWheel>", self._on_mousewheel)
        # self._win.bind("<Motion>", self._motion)
        # self._win.bind("<Button-1>", self._mouseclicked)
        # self._win.columnconfigure(0, weight=1)
        # self._win.rowconfigure(0, weight=1)

        self._cur_path: str = cur_path
        self._res_path: str = os.path.dirname(xmlfile)

        # self._mousex: int = 0
        # self._mousey: int = 0

        self.set_title(self._title)
        self.create_window()

    def _get_scale_factor(self):
        """获取系统缩放比例（默认1.0）"""
        try:
            if sys.platform.startswith("win"):
                # Windows：通过系统API获取缩放比例
                user32 = ctypes.windll.user32
                dpi = cast(float, user32.GetDpiForWindow(user32.GetForegroundWindow()))
                return dpi / 96.0  # 96 DPI为默认缩放（100%）
            elif sys.platform == "darwin":
                # macOS：通过Tk内置方法获取
                return cast(float, self._win.tk.call("tk", "scaling"))
            else:
                # Linux：假设使用1.0或通过xdpyinfo获取（简化处理）
                return 1.0
        except Exception:
            return 1.0  # 异常时使用默认值

    @property
    def win(self):
        return self._win

    @property
    def path(self):
        return self._cur_path

    def debug_print(self,
            *values: object,
            sep: str | None = " ",
            end: str | None = "\n",
            ffile: SupportsWrite[str] | None = None,
            flush: Literal[False] = False):
        if self._is_debug:
            print(*values, sep, end, ffile, flush)

    def _center_window(self, width: int, hight: int):
        """设置窗口居中和宽高

        Args:
            width (int): 窗口宽度
            hight (int): 窗口高度

        Returns:
            None
        """
        # 获取屏幕宽度和高度
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()

        # 计算中心坐标
        cen_x = int((sw - width) / 2)
        cen_y = int((sh - hight) / 2)

        self._xx: int = cen_x
        self._yy: int = cen_y

        # 设置窗口大小并居中
        self._win.geometry(f"{width}x{hight}+{cen_x}+{cen_y}")

    @override
    def set_title(self, val: str):
        super().set_title(val)
        self._win.title(self._title)

    @override
    def create_window(self):
        if self._ww and self._hh:
            self._center_window(self._ww, self._hh)

        for frm in list(self._wincfg):
            # _ = self.create_controls(self._win, frm)
            _ = self.create_controls(self._root, frm)

    @override
    def create_control(self, parent: Widget, ctrl_cfg: et.Element,
            level: int = 0, owner: Dialog | None = None) -> tuple[str, Widget]:
        if owner is None:
            owner = self
        tag = ctrl_cfg.tag
        attr_dict = ctrl_cfg.attrib
        text: str | None = attr_dict.get("text")
        idctrl: str = ""
        if "id" in attr_dict:
            idctrl = attr_dict["id"]
        elif text is not None:
            idctrl = text.replace(" ", "").replace(".", "_").replace("\n", "_")
        else:
            raise RuntimeError("No id")
        self.debug_print(f"{'  '*level}{tag}, id: {idctrl}, text: {text}", end="")

        if idctrl in self._idctrl_dict:
            raise KeyError(f"{idctrl} already exists")

        options: dict[str, Any] = {}
        if "options" in attr_dict:
            options = eval(attr_dict["options"])

        # pe(type(parent))
        if issubclass(type(parent), tkControl):
            master = cast(tkControl, parent).control
        # elif type(parent) is tkWM[tk.Tk]:
            # master = parent.control
        # elif type(parent) is tkWM[tk.Toplevel]:
            # master = parent.control
        elif isinstance(parent, tkWM):
            # typ = get_args(get_origin(parent))
            # if typ == tuple[tk.Tk]:
            master = parent.control
        elif tag == "Menu":
            master = self._win
        else:
            # master = cast(tk.Widget, parent)
            raise ValueError(f"{tag}: unknown Control")

        match tag:
            case "LabelFrame":
                assert text is not None
                # ctrl = ttk.LabelFrame(master, text=text, **options)
                ctrl = LabelFrameCtrl(master, text, idctrl, **options)
                self.debug_print()
            case "Frame" | "Tab":
                ctrl = FrameCtrl(master, idctrl, **options)
                self.debug_print()
            case "ScrollableFrame":
                ctrl = ScrollableFrameCtrl(master, self, idctrl,
                    int(attr_dict["Width"]), int(attr_dict["Height"]),
                    **options)
                self.debug_print()
            case "Label":
                assert text is not None
                # clickable = cast(bool, attr_dict.get("clickable", False))
                clickable = True if "clickable" in attr_dict else False
                ctrl = LabelCtrl(master, owner, idctrl, text, clickable, **options)
            case "Button":
                assert text is not None
                ctrl = ButtonCtrl(master, owner, idctrl, text, **options)
            # TODO
            case "Canvas":
                ctrl = tk.Canvas(master, **options)
            case "Combobox":
                ctrl = ComboboxCtrl(master, owner,
                    idself=idctrl,
                    default=int(attr_dict["default"]),
                    **options)
            case "Entry":
                ctrl = EntryCtrl(master, **options)
            case "ImageButton":
                ctrl = ImageBtttonCtrl(master, owner, idctrl,
                    respath=self._res_path, imagefile=attr_dict["image"],
                    text=text, **options)
            case "ImagePanel":
                image = attr_dict.get("image", "")
                if image:
                    image = os.path.join(self._res_path, image)
                ctrl = ImagePanelCtrl(master, idctrl, image, **options)
            case "MatPlot":
                assert text is not None
                if "size" in attr_dict:
                    size = cast(tuple[float, float], literal_eval(attr_dict["size"]))
                    ctrl = MatPlotCtrl(master, idctrl, text, attr_dict["xLabel"],
                        attr_dict["yLabel"], size)
                else:
                    ctrl = MatPlotCtrl(master, idctrl, text, attr_dict["xLabel"],
                        attr_dict["yLabel"])
            case "Menu":
                self.debug_print()
                ctrl = self.create_menu(ctrl_cfg, **options)
                _ = self._win.config(menu=ctrl)
            case "RadiobuttonGroup":
                assert text is not None
                ctrl = RadioButtonGroupCtrl(master, self, owner, idctrl,
                    text=text, subctrlcfg=ctrl_cfg,
                    level=level, **options)
                self.debug_print()
            case "Radiobutton":
                assert text is not None
                if "var" in attr_dict:
                    var_text = "_" + attr_dict["var"]
                else:
                    var_text = "_var" + attr_dict["text"].replace(" ", "") \
                        .replace(".", "_").replace("\n", "_")
                val = int(attr_dict["value"])
                ctrl = RadioButtonCtrl(master, owner, idctrl,
                    text=text, vartext=var_text, value=val, **options)
            case "Checkbutton":
                assert text is not None
                if "var" in attr_dict:
                    vartext = attr_dict["var"]
                else:
                    vartext = attr_dict["text"].replace(" ", "").replace(".", "_").replace("\n", "_")
                # sel = cast(bool, literal_eval(attr_dict.get("select", "False")))
                sel = True if "select" in attr_dict else False
                ctrl = CheckButtonCtrl(master, self, idctrl,
                    text=text, vartext=vartext, select=sel, **options)
            case "Statusbar":
                ctrl = MultiStatusBar(master, **options)
                # for subctrl_cfg in list(ctrl_cfg):
                    # ctrl.set_label(**subctrl_cfg.attrib)
            # TODO
            case "ScrolledText":
                ctrl = scrolledtext.ScrolledText(master, **options)
            # TODO
            case "Spinbox":
                ctrl = tk.Spinbox(master,
                    command=lambda: self.process_message(idctrl, event="Changed"),
                    **options)
            # TODO
            case "Style":
                ctrl = ttk.Style()
                ctrl.configure(text, **options)
            case "Toolbar":
                ctrl = ToolbarCtrl(master, self, self._res_path,
                    list(ctrl_cfg), **options)
                self.debug_print()
            # TODO
            case "Scrollbar":
                ctrl = tk.Scrollbar(master.control)
                ctrl.configure(**options)
            case "Listbox":
                ctrl = ListboxCtrl(master, idctrl, **options)
            case "PicsListview":
                ctrl = PicsListviewCtrl(master, self, owner, idctrl,
                    int(attr_dict["num_column"]), int(attr_dict["pic_size"]),
                    self._res_path)
            case "Dialog":
                ctrl = DialogCtrl(master, self, idctrl, title=text,
                    width=int(attr_dict["Width"]), height=int(attr_dict["Height"]),
                    subctrlcfg_list=list(ctrl_cfg), **options)
                self.debug_print()
            case "Notebook":
                ctrl = NotebookCtrl(master, self, idctrl,
                    subctrlcfg_list=list(ctrl_cfg), level=level, **options)
            case _:
                raise ValueError(f"{tag}: unknown Control")

        if "tooltip" in attr_dict:
            if tag in ["Canvas", "ScrolledText", "Spinbox", "Style", "Scrollbar"]:
                Hovertip(ctrl, attr_dict["tooltip"], hover_delay=500)
            else:
                Hovertip(ctrl.control, attr_dict["tooltip"], hover_delay=500)

        self._idctrl_dict[idctrl] = ctrl

        return idctrl, ctrl

    @override
    def assemble_control(self, ctrl: Widget, attr_dict: dict[str, str],
            prefix: str = ""):

        ctrl_type = type(ctrl)
        # pe(ctrl_type)
        if ctrl_type in [tk.Menu, DialogCtrl]:
            return
        elif ctrl_type in [tk.Canvas,  scrolledtext.ScrolledText, tk.Spinbox, \
            ttk.Style, tk.Scrollbar]:
            widget = cast(tk.Widget, ctrl)
        elif ctrl_type is ScrollableFrameCtrl:
            widget = cast(ScrollableFrameCtrl, ctrl).outter
        else:
            widget = cast(tkControl, ctrl).control

        if "layout" in attr_dict:
            if attr_dict["layout"] == "pack":
                widget.pack(**(literal_eval(attr_dict["pack"])))
            elif attr_dict["layout"] == "grid":
                widget.grid(**(literal_eval(attr_dict["grid"])))
            elif attr_dict["layout"] == "place":
                widget.place(**(literal_eval(attr_dict["place"])))
            else:
                self.debug_print(f"{prefix}, unknown layout of {attr_dict['layout']}")
                return
        else:
            # self._debug_print(f"{attr_dict['text']}: no assemble")
            return

        if "childOpt" in attr_dict:
            for child in ctrl.control.winfo_children():
                child.grid_configure(**(literal_eval(attr_dict["childOpt"])))

        self.debug_print(f"{prefix}, layout: {attr_dict['layout']}")

    def create_menu(self, rootcfg: et.Element, **kwargs: object) -> tk.Menu:
        menubar = tk.Menu(self._win, **kwargs)

        # def get_cmd(cmd_name, msg, ext_msg=""):
        def get_cmd(cmd_name: str, **kwargs):
            # return lambda: self.process_message(cmd_name, msg, ext_msg)
            return lambda: self.process_message(cmd_name, **kwargs)

        # def get_cmd_e(cmd_name, msg, ext_msg=""):
        def get_cmd_e(cmd_name: str, **kwargs):
            # return lambda event: self.process_message(cmd_name, msg, ext_msg)
            return lambda event: self.process_message(cmd_name, **kwargs)

        for menucfg in list(rootcfg):
            attr_dict = menucfg.attrib
            label = attr_dict["Header"]
            self.debug_print(f"  Menu: {label}")
            menu = tk.Menu(menubar, tearoff=False)

            if "options" in attr_dict:
                options = literal_eval(attr_dict["options"])
            else:
                options = {}

            for submenucfg in list(menucfg):
                tag = submenucfg.tag
                subattr_dict = submenucfg.attrib
                if tag == "Separator":
                    menu.add_separator()
                    self.debug_print(f"    subMenu: {submenucfg.tag}")
                    continue
                if "options" in subattr_dict:
                    sub_options = literal_eval(subattr_dict["options"])
                else:
                    sub_options = {}
                sub_label = subattr_dict["Command"]
                if "id" in subattr_dict:
                    idmenu = subattr_dict["id"]
                else:
                    idmenu = str(sub_label.replace(" ", "").replace("...", ""))
                self.debug_print(f"    subMenu: {tag} -> {sub_label}")
                if tag == "Checkbutton":
                    var_name = subattr_dict["variable"]
                    self.__dict__[f"_{var_name}"] = tk.BooleanVar()
                    var = self.__dict__[f"_{var_name}"]
                    # var.set(True)
                    # msg = "Changed"
                    # ext_msg = var.get()
                    # cmd = get_cmd(cmd_name, msg, ext_msg)
                    kwargs = {"event": "Changed", "val": var.get()}
                    cmd = get_cmd(idmenu, **kwargs)
                    menu.add_checkbutton(
                        label=sub_label, command=cmd, variable=var, **sub_options
                    )
                elif tag == "MenuItem":
                    # msg = "Clicked"
                    # ext_msg = ""
                    kwargs = {"event": "Clicked"}
                    # cmd = get_cmd(cmd_name, msg, ext_msg)
                    cmd = get_cmd(idmenu, **kwargs)
                    menu.add_command(label=sub_label, command=cmd, **sub_options)
                else:
                    raise ValueError(f"    Unknown Menu: {tag} -> {sub_label}")

                if "accelerator" in sub_options:
                    shortcut_lst = sub_options["accelerator"].split("+")
                    shortcut = (
                        "<"
                        + shortcut_lst[0].replace("Ctrl", "Control").strip()
                        + "-"
                        + shortcut_lst[1].lower().strip()
                        + ">"
                    )
                    # pv(shortcut)
                    # cmd = get_cmd_e(cmd_name, msg, ext_msg)
                    cmd = get_cmd_e(idmenu, **kwargs)
                    self._win.bind_all(shortcut, cmd)

            menubar.add_cascade(label=label, menu=menu, **options)

        return menubar

    def show_info(self, title: str = "", message: str = ""):
        tkMessageBox.showinfo(title, message)

    def show_warn(self, title: str = "", message: str = ""):
        tkMessageBox.showwarning(title, message)

    @override
    def show_err(self, title: str = "", message: str = ""):
        tkMessageBox.showerror(title, message)

    def ask_yesno(self, title: str = "", message: str = ""):
        return tkMessageBox.askyesno(title, message)

    """
    @override
    def process_message(self, idmsg: str, **kwargs):
        if idmsg in ["Exit", "Quit"]:
            self.exit_window()
            return
        return MsgLoop.process_message(self, idmsg, **kwargs)
    """

    @override
    def go(self):
        WinBasic.register_eventhandler(self, "Exit", self.exit)
        WinBasic.register_eventhandler(self, "Quit", self.exit)

        super().back(False)

        # self._x = self._win.winfo_rootx()
        # self._y = self._win.winfo_rooty()

        self._win.focus_force()
        # self._win.focus_set()

        self._win.mainloop()

    def _on_winresize(self, event: tk.Event[tk.Misc]):
        """ listen events of window resizing.
        """
        if event is not None:
            if self._ww != self._win.winfo_width() or self._hh != self._win.winfo_height():
                if self._ww != self._win.winfo_width():
                    self._ww = self._win.winfo_width()
                if self._hh != self._win.winfo_height():
                    self._hh = self._win.winfo_height()
                self.process_message("WindowResize", w=self._ww, h=self._hh)

    def _on_keypress(self, event: tk.Event[tk.Misc]):
        """
            event.state
            0x0001 	Shift.          0x0004 	Control.
            0x0002 	Caps Lock.      0x0010 	Num Lock.
            0x0008 	Left-hand Alt.  0x0080 	Right-hand Alt.
            0x0100 	Mouse button 1. 0x0200 	Mouse button 2.
            0x0400 	Mouse button 3
        """
        state=event.state
        pv(state)
        ctrl = (state & 0x0004) >> 2
        shift = state & 0x0001
        # alt = state & 0x0008 | state & 0x0080
        self.process_message("KeyPress", key=event.keysym, ctrl=ctrl, shift=shift)

    def exit(self, **kwargs: object):
        res = tkMessageBox.askquestion(
            "Exit Application", "Do you really want to exit?"
        )
        if res == "yes":
            super().destroy()
            self._win.destroy()


if __name__ == "__main__":
    class ExampleApp(tkWin):
        def __init__(self, cur_path: str, xmlfile: str):
            super().__init__(cur_path, xmlfile)
            self._i: int = 0
            self._idx_left_vertical: int = 0
            self._idx_left_horizontal: int = 0
            self._idx_right_vertical: int = 0
            self._idx_right_horizontal: int = 0
            self._hourdetail_dlg: DialogCtrl = cast(DialogCtrl,
                self.get_control("dlgHourDetail"))

        def _create_label(self, parent: tkControl, lid: str, rowid: int, txt: str):
            lbl_xml = self.create_xml("Label", {"text": txt, "id": lid})
            _, lbl_ctrl = self.create_control(parent, lbl_xml)
            self.assemble_control(lbl_ctrl, {"layout":"grid",
                "grid":f"{{'row':{rowid},'column':0,'sticky':'w'}}"})

        @override
        def process_message(self, idmsg: str, **kwargs: object):
            match idmsg:
                case "meuShowInfoBox":
                    self.show_info('Python Message Info Box', '通知：程序运行正常！')
                case "WarnBox":
                    self.show_warn('Python Message Warning Box', '警告：程序出现错误，请检查！')
                case "ErrorBox":
                    self.show_err('Python Message Error Box', '错误：程序出现严重错误，请退出！')
                case "ChoiceBox":
                    answer = self.ask_yesno("Python Message Dual Choice Box", "你喜欢这篇文章吗？\n您的选择是：")
                    if answer:
                        self.show_info('显示选择结果', '您选择了“是”，谢谢参与！')
                    else:
                        self.show_info('显示选择结果', '您选择了“否”，谢谢参与！')
                case "varRadSel":
                    values = ["富强民主", "文明和谐", "自由平等", "公正法治", "爱国敬业", "诚信友善"]
                    monty2 = cast(ttk.LabelFrame, self.get_control("控件示范区2"))
                    monty2.configure(text=values[int(kwargs["val"])])
                case "varChkEna":
                    check_btn = cast(CheckButtonCtrl, self.get_control("遵从内心"))
                    if int(kwargs["val"]) == 1:
                        check_btn.disable()
                    else:
                        check_btn.enable()
                case "varChkUne":
                    # check_btn = cast(CheckButtonCtrl, self.get_control("屈于现实"))
                    # if int(kwargs["val"]) == 1:
                        # check_btn.disable()
                    # else:
                        # check_btn.enable()
                    pass
                case "点击之后_按钮失效":
                    btn = cast(ButtonCtrl, self.get_control("点击之后_按钮失效"))
                    name = self.get_control("name")
                    btn.configure(text='Hello\n ' + name.get_val())
                    # self.disable_control(btn)
                    btn.disable()
                case "blankSpin":
                    spin = cast(tk.Spinbox, self.get_control("blankSpin"))
                    value = spin.get()
                    scr = cast(scrolledtext.ScrolledText, self.get_control("scrolledtext"))
                    scr.insert(tk.INSERT, value + '\n')
                case "bookSpin":
                    spin = cast(tk.Spinbox, self.get_control("bookSpin"))
                    value = spin.get()
                    scr = cast(scrolledtext.ScrolledText, self.get_control("scrolledtext"))
                    scr.insert(tk.INSERT, value + '\n')
                case "btnHaa":
                    ctrl = cast(ListboxCtrl, self.get_control("lstHaa"))
                    self._i += 1
                    ctrl.insert("end", f"第{self._i:02}项")
                case "btnLeftVAdd":
                    ctrl = cast(ScrollableFrameCtrl, self.get_control("frmLeftContentArea"))
                    self._idx_left_vertical += 1
                    num_row = self._idx_left_vertical
                    id_lbl = f"lblLeftV{num_row}"
                    self._create_label(ctrl, id_lbl, num_row, f"垂直内容{num_row}")
                case "btnLeftVSub":
                    id_lbl = f"lblLeftV{self._idx_left_vertical}"
                    self.delete_control(id_lbl)
                    self._idx_left_vertical -= 1
                case "btnLeftHAdd":
                    ctrl = cast(ScrollableFrameCtrl, self.get_control("frmLeftContentArea"))
                    self._idx_left_horizontal += 1
                    num_row = self._idx_left_horizontal
                    id_lbl = f"lblLeftH{num_row}"
                    self._create_label(ctrl, id_lbl, num_row, f"{'水平内容'*num_row}")
                case "btnLeftHSub":
                    id_lbl = f"lblLeftH{self._idx_left_horizontal}"
                    self.delete_control(id_lbl)
                    self._idx_left_horizontal -= 1
                case "btnRightVAdd":
                    ctrl = cast(ScrollableFrameCtrl, self.get_control("frmRightContentArea"))
                    self._idx_right_vertical += 1
                    num_row = self._idx_right_vertical
                    id_lbl = f"lblRightV{num_row}"
                    self._create_label(ctrl, id_lbl, num_row, f"垂直内容{num_row}")
                case "btnRightVSub":
                    id_lbl = f"lblRightV{self._idx_right_vertical}"
                    self.delete_control(id_lbl)
                    self._idx_right_vertical -= 1
                case "btnRightHAdd":
                    ctrl = cast(ScrollableFrameCtrl, self.get_control("frmRightContentArea"))
                    self._idx_right_horizontal += 1
                    num_row = self._idx_right_horizontal
                    id_lbl = f"lblRightH{num_row}"
                    self._create_label(ctrl, id_lbl, num_row, f"{'水平内容'*num_row}")
                case "btnRightHSub":
                    id_lbl = f"lblRightH{self._idx_right_horizontal}"
                    self.delete_control(id_lbl)
                    self._idx_right_horizontal -= 1
                case "About":
                    # x, y = cast(tuple[int, int], kwargs["mousepos"])
                    x, y = self._xx, self._yy
                    self._hourdetail_dlg.do_show(self, x+20, y+20, **kwargs)
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True

    filepath = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        filepath = os.path.dirname(os.path.abspath(sys.executable))
    winsample_xml = os.path.join(filepath, "resources", "windowSample.xml")
    eapp = ExampleApp(filepath, winsample_xml)
    eapp.go()
