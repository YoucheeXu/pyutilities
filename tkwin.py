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
from typing import Literal, Any, override, cast
from typing import Protocol, TypeVar
# from collections.abc import Callable

import tkinter as tk
import tkinter.messagebox as tkMessageBox
from tkinter import ttk
from tkinter import scrolledtext
import xml.etree.ElementTree as et
from ast import literal_eval

import cv2
# from PIL import Image, ImageTk    # for imgButton
import PIL

from idlelib.statusbar import MultiStatusBar
from idlelib.tooltip import Hovertip

try:
    from logit import pv, pe, po
    from tkcontrol import tkControl
    from matplot import MatPlotCtrl
    from winbasic import EventHanlder, Dialog, WinBasic
    import cv2_utilities as cv2u
except ImportError:
    from pyutilities.logit import pv, pe, po
    from pyutilities.tkcontrol import tkControl
    from pyutilities.matplot import MatPlotCtrl
    from pyutilities.winbasic import EventHanlder, Dialog, WinBasic
    import pyutilities.cv2_utilities as cv2u


__version__ = "4.3.3"
IS_WINDOWS = platform.system() == "Windows"


class LabelCtrl(tkControl):
    def __init__(self, parent: tk.Widget, owner: Dialog, idself: str,
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
    def __init__(self, parent: tk.Widget, **options: Any):
        ctrl = ttk.Entry(parent)
        super().__init__(parent, "", "", ctrl)
        self._var: tk.StringVar = tk.StringVar()
        _= ctrl.configure(textvariable=self._var, **options)

    def get_val(self) -> str:
        return self._var.get()

    def set_val(self, val: str):
        self._var.set(val)


class ImagePanelCtrl(tkControl):
    # def __init__(self, parent: tk.Widget, imagefile: str = "", **options: int):
    def __init__(self, parent: tk.Widget, idself: str, imagefile: str, *,
            width: int = 0, height: int = 0, **options: Any):
        # self._parent: tk.Widget = parent
        # tk.Label.__init__(self, parent)
        ctrl = tk.Label(parent)
        super().__init__(parent, "", idself, ctrl)
        """
        width: int = options.get("width", 0)
        # self._hh: int = 0
        if hh := options.get("height", 0):
            height: int = hh
        else:
            height = width if width else 0
        """
        self.image: tk.Image | None = None
        if imagefile:
            # image: tk.Image = self.read_image(img_file, options["width"], options["height"])
            image: tk.Image = self._read_image(imagefile, width, height)
            _ = ctrl.configure(text="", image=image, anchor=tk.CENTER, **options)
            self.image = image
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
        image2 = PIL.Image.fromarray(image)
        # ...and then to ImageTk format
        image3 =  cast(tk.Image, PIL.ImageTk.PhotoImage(image2))
        return image3

    def display_image(self, image: cv2.typing.MatLike):
        # OpenCV represents images in BGR order however PIL represents
        # images in RGB order, so we need to swap the channels
        # image1 = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image1 = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # convert the images to PIL format...
        image2 = PIL.Image.fromarray(image1)

        # ...and then to ImageTk format
        image3 = cast(tk.Image, PIL.ImageTk.PhotoImage(image2))

        _ = cast(tk.Label, super().control).configure(image=image3)
        self.image = image3


class ButtonCtrl(tkControl):
    def __init__(self, parent: tk.Widget, owner: Dialog, idself: str, text: str, **options: Any):
        ctrl = ttk.Button(parent, text=text, **options)
        tkControl.__init__(self, parent, text, idself, ctrl)
        self._owner: Dialog = owner
        # _ = ctrl.configure(command=lambda btn=ctrl: owner.process_message(idself,
            # mousepos=(btn.winfo_rootx(), btn.winfo_rooty())))
        _ = ctrl.configure(command=self._btn_clicked, **options)

    def _btn_clicked(self):
        btn = cast(ttk.Button, self._tkctrl)
        self._owner.process_message(self._idself,
            mousepos=(btn.winfo_rootx(), btn.winfo_rooty()))


class ImageBtttonCtrl(tkControl):
    def __init__(self, parent: tk.Widget, owner: Dialog, idself: str, *,
            respath: str, imagefile: str, text: str | None, width: int = 0, height: int = 0,
            **options: Any):
        ctrl = tk.Button(parent, **options)
        title = text if text else ""
        tkControl.__init__(self, parent, title, idself, ctrl)
        self._res_path: str = respath
        self._ww: int = width
        """
        # self._hh: int = 0
        if hh := height:
            self._hh: int = hh
        else:
            self._hh = self._ww if self._ww else 0
        """
        self._hh: int = height if height else width if width else 0

        # self._app: GuiBasic =
        imagefile = os.path.join(self._res_path, imagefile)
        eimg = self._read_image(imagefile, self._ww, self._hh)
        if eimg is None:
            raise RuntimeError(f"fail to read image: {imagefile}")

        def cmd():
            owner.process_message(idself,
                mousepos=(ctrl.winfo_rootx(), ctrl.winfo_rooty()))

        if text is not None:
            _ = ctrl.configure(text=text, image=eimg, command=cmd, compound=tk.LEFT,
                relief=tk.FLAT, **options)
                # **options)
        else:
            _ = ctrl.configure(image=eimg, command=cmd, relief=tk.FLAT, **options)
        self.image: tk.Image = eimg

    def _read_image0(self, imagepath: str, w: int, h: int) -> tk.Image | None:
        eimg: tk.Image | None = None
        image = PIL.Image.open(imagepath)
        if w:
            image = image.resize((w, h))
        photoimage = cast(tk.Image, PIL.ImageTk.PhotoImage(image))
        return photoimage

    def _read_image(self, imagepath: str, w: int, h: int):
        image = cv2.imread(imagepath, cv2.IMREAD_UNCHANGED)
        if w:
            image = cv2.resize(image, (w, h), interpolation=cv2.INTER_CUBIC)
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # convert the images to PIL format...
        image2 = PIL.Image.fromarray(image)
        # ...and then to ImageTk format
        image3 =  cast(tk.Image, PIL.ImageTk.PhotoImage(image2))
        return image3

    # TODO: wait to test
    def change_image(self, imagefile: str, w: int = 0, h: int = 0):
        imagefile = os.path.join(self._res_path, imagefile)
        if not w:
            w, h = self._ww, self._hh
        photo = self._read_image(imagefile, w, h)
        if photo is not None:
            btn = cast(tk.Button, super().control)
            _ = btn.configure(image=photo)
            # btn.image = photo
            self.image = photo


class CheckButtonCtrl(tkControl):
    def __init__(self, parent: tk.Widget, owner: Dialog, idself: str, *,
            text: str, vartext: str, select: bool, **options: Any):
        ctrl = tk.Checkbutton(parent)
        tkControl.__init__(self, parent, "", idself, ctrl)
        # self._app: GuiBasic = app
        self._vartext: str = "_" + vartext
        self.__dict__[self._vartext] = tk.IntVar()
        # if self._vartext not in app.__dict__:
            # app.__dict__[self._vartext] = tk.IntVar()
        # self._var: tk.IntVar = tk.IntVar()
        variable = cast(tk.IntVar, self.__dict__[self._vartext])
        # variable = cast(tk.IntVar, app.__dict__[self._vartext])
        _ = ctrl.configure(text=text,
            variable=variable, **options)

        # trace_add(self, mode: Literal["array", "read", "write", "unset"],
            # callback: Callable[[str, str, str], object])
        _ = variable.trace_add("write",
            lambda u0, u1, u2: owner.process_message(vartext, event="Changed", val=variable.get()))

        if select:
            ctrl.select()

    def get_val(self) -> int:
        # return cast(tk.IntVar, self._app.__dict__[self._vartext]).get()
        return cast(tk.IntVar, self.__dict__[self._vartext]).get()


class ComboboxCtrl(tkControl):
    def __init__(self, parent: tk.Widget, owner: Dialog, *,
            idself: str, default: int, **options: Any):
        ctrl = ttk.Combobox(parent)
        super().__init__(parent, "", idself, ctrl)
        self._var: tk.StringVar = tk.StringVar()
        _ = ctrl.configure(textvariable=self._var, **options)
        _ = ctrl.current(default)
        _ = self.bind(
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
    def __init__(self, parent: tk.Widget, idself: str,
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
    def __init__(self, parent: tk.Widget, owner: Dialog, idself: str, *,
            text: str, vartext: str, value: int, **options: Any):
        ctrl = ttk.Radiobutton(parent)
        tkControl.__init__(self, parent, "", idself, ctrl)
        # self._app: GuiBasic = app
        self._master: Dialog = owner
        self._vartext: str = "_" + vartext
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


class RadioButtonGroupCtrl(ttk.LabelFrame):
    def __init__(self, parent: tk.Misc, app: WinBasic, owner: Dialog, idself: str, *,
            text: str, subctrlcfg: et.Element,
            level: int, **options: Any):
        super().__init__(parent)
        self._idself: str = idself
        self._var_val: tk.IntVar = tk.IntVar()
        self._app: WinBasic = app
        self._owner: Dialog = owner
        # pv(options)
        _ = self.configure(text=text, **options)
        self._radbutton_lst: list[ttk.Radiobutton] = []
        _ = self._create_subctrls(subctrlcfg, level)

    def get_val(self) -> int:
        return self._var_val.get()

    def set_val(self, val: int):
        self._var_val.set(val)

    def _create_subctrls(self, subctrls: et.Element, level: int):
        for subctrl_cfg in subctrls:
            radbtn_attr_dict = subctrl_cfg.attrib
            val = int(radbtn_attr_dict["value"])
            text: str = radbtn_attr_dict["text"]
            sub_ctrl = self._add_radiobutton(value=val, text=text,
                command=lambda: self._owner.process_message(
                    self._idself, event="Changed", val=self.get_val()))
            # self._app.debug_print(f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
            self._app.assemble_control(sub_ctrl, radbtn_attr_dict)

    def _add_radiobutton(self, **opt_dict: Any):
        radbutton = ttk.Radiobutton(master=self, variable=self._var_val, **opt_dict)
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
    def __init__(self, parent: tk.Widget, app: WinBasic, idself: str, *,
            subctrlcfg_list: list[et.Element], level: int, **options: Any):
        ctrl = ttk.Notebook(parent, **options)
        tkControl.__init__(self, parent, "", idself, ctrl)
        # app.debug_print()
        self._app: WinBasic = app
        self._idself: str = idself
        self._idctrl_list: list[str] = []
        for subctrl_cfg in list(subctrlcfg_list):
            id_, sub_ctrl = self._app.create_control(ctrl,
                subctrl_cfg, level + 1)
            self._idctrl_list.append(id_)
            # app.debug_print(f"tabCtrl: {subctrl_cfg.tag}")
            ctrl.add(cast(tk.Widget, sub_ctrl),
                text=subctrl_cfg.attrib["text"])
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
    def __init__(self, parent: tk.Widget, idself: str, **options):
        tkControl.__init__(self, parent, "", idself, tk.Frame(parent, **options))

    @override
    def destroy(self):
        po(f"FrameCtrl {self._idself} destroy")
        super().destroy()


# TODO: not fininsed
class LabelFrameCtrl(tkControl):
    def __init__(self, parent: tk.Widget, title:str, idself: str, **options):
        ctrl = ttk.LabelFrame(parent, text=title, **options)
        tkControl.__init__(self, parent, title, idself, ctrl)

    @override
    def destroy(self):
        po(f"LabelFrameCtrl {self._idself} destroy")
        super().destroy()


class ScrollableFrameCtrl(tkControl):
    """ VerticalScrollableFrameCtrl
    """
    def __init__(self, parent: tk.Widget, app: WinBasic, idself: str,
            width: int = 0, height: int = 0, **options: Any):
        outter = tk.Frame(parent, **options)
        super().__init__(parent, "", idself, outter)
        self._canvas: tk.Canvas = tk.Canvas(outter, width=width, height=height)
        # Create a frame inside the canvas which will be scrolled with it
        self._interior: ttk.Frame = ttk.Frame(self._canvas)

        self._vscrollbar: ttk.Scrollbar = ttk.Scrollbar(outter, orient="vertical", command=self._canvas.yview)

        """
        _ = self._interior.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            )
        )
        """
        _ = self._interior.bind('<Configure>', self._configure_interior)
        _ = self._canvas.bind('<Configure>', self._configure_canvas)

        self._interior_id: int = self._canvas.create_window((0, 0),
            window=self._interior, anchor="nw")
        _ = self._canvas.configure(yscrollcommand=self._vscrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        # self._vscrollbar.pack(side="right", fill="y")
        self._vscrollbar.pack(side="right", fill="y", expand=False)
        # 绑定滚动条事件
        # _ = self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        app.register_eventhandler("MouseWheel", self._on_mousewheel)

    def _configure_interior(self, event: tk.Event[ttk.Frame]):
        # Update the scrollbars to match the size of the inner frame
        size = (self._interior.winfo_reqwidth(), self._interior.winfo_reqheight())
        _ = self._canvas.config(scrollregion=(0, 0, size[0], size[1]))
        if self._interior.winfo_reqwidth() != self._canvas.winfo_width():
            # Update the canvas's width to fit the inner frame
            _ = self._canvas.config(width=self._interior.winfo_reqwidth())

    def _configure_canvas(self, event: tk.Event[tk.Canvas]):
        if self._interior.winfo_reqwidth() != self._canvas.winfo_width():
            # Update the inner frame's width to fill the canvas
            _ = self._canvas.itemconfigure(self._interior_id, width=self._canvas.winfo_width())

    # def _on_mousewheel(self, event: tk.Event[tk.Canvas]):
    def _on_mousewheel(self, **kwargs: Any):
        if not self._backed:
            # delta = cast(tk.Event[tk.Widget], kwargs["event"]).delta
            delta = cast(int, kwargs["delta"])
            scroll_direction = -1 if delta > 0 else 1
            self._canvas.yview_scroll(scroll_direction, "units")

    @override
    @property
    def control(self):
        return self._interior

    @override
    def destroy(self):
        po(f"ScrollableFrame {self._idself} destroy")
        self._interior.destroy()
        self._vscrollbar.destroy()
        # self._canvas.unbind_all("<MouseWheel>")
        # self._canvas.unbind("<MouseWheel>")
        self._canvas.destroy()
        super().destroy()


# TODO: 1. Tip
class PicsListviewCtrl(tkControl):
    def __init__(self, parent: tk.Widget, app: WinBasic, owner: Dialog, idself: str,
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
            image_panel.grid(row=i // self._num_column, column=i % self._num_column,
                padx=self._spacing, pady=self._spacing)
            _= image_panel.bind("<Button-1>",
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
    def __init__(self, parent: tk.Widget, app: WinBasic, res_path: str,
            subctrls: list[et.Element], **options):
        ctrl = ttk.Frame(parent, **options)
        tkControl.__init__(self, parent, "", "", ctrl)
        self._res_path: str = res_path
        self._app: WinBasic = app
        self._idctrl_list: list[str] = []
        for subctrl in subctrls:
            idctrl_list = self._app.create_controls(ctrl, subctrl, 1)
            self._idctrl_list.extend(idctrl_list)

    @override
    def destroy(self):
        for idctrl in self._idctrl_list:
            self._app.delete_control(idctrl)
        self._idctrl_list.clear()
        super().destroy()


# TODO: auto scrollable or not
class DialogCtrl(Dialog):
    def __init__(self, parent: tk.Widget, app: WinBasic, idself: str, *,
            title: str, width: int, height: int,
            subctrlcfg_list: list[et.Element], **options: Any):
        super().__init__(title, width, height)
        self._parent: tk.Widget = parent
        self._owner: Dialog | None = None
        self._top: tk.Toplevel | None = None
        self._app: WinBasic = app
        self._alive: bool = False
        self._idself: str = idself
        self._subctrlcfg_list: list[et.Element] = subctrlcfg_list
        self._idctrl_list: list[str] = []
        self._extral_msg: dict[str, Any] = {}

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
            self._top.title(self._title)

    @property
    def alive(self):
        return self._alive

    def do_show(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: Any):
        po(f"show Dialog {self._idself}: {kwargs}")
        # self.deiconify()
        self._alive = True
        if owner is not None:
            self._owner = owner

        self._top = tk.Toplevel(self._parent)

        # x, y, _, _ = self._app.get_winsize()
        if owner is not None:
            self._xx, self._yy = x, y
            # pv(owner.pos)
            # po(f"owner is {owner.title}")
        else:
            self._xx = self._parent.winfo_rootx() + x
            self._yy = self._parent.winfo_rooty() + y

        # pv(self.pos)

        self._top.geometry(f'{self._ww}x{self._hh}+{self._xx}+{self._yy}')
     
        # self.withdraw()
        iddlg = self._idself

        frmdlg_xml = self._app.create_xml("Top", {})

        id_frmain = f"frmMain{iddlg}"
        # frmain_xml = self._app.create_xml("Frame", {"id": id_frmain}, frmdlg_xml)
        frmain_xml = self._app.create_xml("ScrollableFrame", {"id": id_frmain,
            "Width": f"{self._ww-30}", "Height": f"{self._hh-160}"}, frmdlg_xml)
        _, frmmain = self._app.create_control(self._top,
            frmain_xml, 0, self)
        # self._idctrl_list.append(id_frmain)
        self._idctrl_dict[id_frmain] = frmmain
        frm_main = frmmain.control

        for sub_ctrl in self._subctrlcfg_list:
            subidctrl_dict = self._app.create_controls(frm_main, sub_ctrl, 1, self)
            # self._idctrl_list.extend(subidctrl_list)
            self._idctrl_dict.update(subidctrl_dict)

        _ = self._app.assemble_control(frmmain, {"layout": "pack",
            "pack": "{'side':'top','fill':'both','expand':True,'padx':5,'pady':5}"})

        frmbot_xml = self._app.create_xml("Frame", {"id": f"frmBot{iddlg}"}, frmdlg_xml)
        id_frmbot, frm_bot = self._app.create_control(self._top,
            frmbot_xml, 0, self)
        # self._idctrl_list.append(id_frmbot)
        self._idctrl_dict[id_frmbot] = frm_bot

        xml = self._app.create_xml("Button", {"id": f"btnConfirm{iddlg}",
            "text": "Confirm", "options": "{'width':20}"}, frmbot_xml)
        idctrl, ctrl = self._app.create_control(frm_bot, xml, 1, self)
        # self._idctrl_list.append(idctrl)
        self._idctrl_dict[idctrl] = ctrl
        _ = self._app.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")

        xml = self._app.create_xml("Button", {"id": f"btnCancel{iddlg}",
            "text": "Cancel", "options": "{'width':20}"}, frmbot_xml)
        idctrl, ctrl = self._app.create_control(frm_bot, xml, 1, self)
        # self._idctrl_list.append(idctrl)
        self._idctrl_dict[idctrl] = ctrl
        # pv(self._idctrl_list)
        _ = self._app.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")

        _ = self._app.assemble_control(frm_bot, {"layout": "pack",
            "pack": "{'side':'bottom','fill':'x','expand':True,'padx':5,'pady':5}"})

        # for idctrl in self._idctrl_list:
            # msg_handler = partial(super().process_message, idctrl)
            # self._app.register_eventhandler(idctrl, msg_handler)

        """
        try:
            before_go = getattr(self, "_before_go")  # get before_go from child
            before_go()
        except AttributeError as r:
            po(f"{self._title} Warnning to go: {r}")
        """
        self._extral_msg = kwargs
        _ = self.process_message("beforego", **kwargs)

        self._top.title(self._title)
        # self._top.update()
        # winfo_x()
        # winfo_y()
        # self._ww = self._top.winfo_width()
        # self._hh = self._top.winfo_height()

        # Disable the window's resizing capability
        _ = self._top.resizable(width=tk.FALSE, height=tk.FALSE)
        # self._top.wait_visibility() # can't grab until window appears, so we wait
        self._top.transient(self._parent)   # dialog window is related to main
        self._top.protocol("WM_DELETE_WINDOW", self.destroy) # intercept close button

        Dialog.register_eventhandler(self, "btnCancel" + self._idself, self._do_cancel)
        # Dialog.register_eventhandler(self, "btnCancel" + self._idself,
            # lambda mousepos: self._do_cancel(**kwargs))
        Dialog.register_eventhandler(self, "btnConfirm" + self._idself, self._do_confirm)

        if self._owner is not None:
            self._owner.back()
        super().back(False)

        # 设置achieved_value，使该窗口始终处于其他窗口的上层
        self._top.attributes("-topmost", True)
        self._top.grab_set()        # ensure all input goes to our window
        self._top.wm_deiconify()
        # self._parent.wait_window(self._top)
        self._top.wait_window()
        # pv(self._id_list)

    def get_control(self, idctrl: str) -> object:
        return self._app.get_control(idctrl)

    def _do_cancel(self, **kwargs: Any):
        po(f"Dialog {self._idself} _do_cancel")
        # pv(kwargs)
        # self._confirm = False
        self.destroy(confirm=False, **kwargs)

    def _do_confirm(self, **kwargs: Any):
        po(f"Dialog {self._idself} _do_confirm")
        # pv(kwargs)
        # self._confirm = True
        self.destroy(confirm=True, **kwargs)

    @override
    def process_message(self, idmsg: str, **kwargs):
        # if idmsg == "btnCancel" + self._idself:
            # self._do_cancel()
        # elif idmsg == "btnConfirm" + self._idself:
            # self._do_confirm()
        # else:
            # return super().process_message(idmsg, **kwargs)
        # return True
        # po(f"{idmsg}: {kwargs}")
        kwargs.update(self._extral_msg)
        # return super().process_message(idmsg, **self._extral_msg, **kwargs)
        return super().process_message(idmsg, **kwargs)

    @override
    def destroy(self, **kwargs: Any):
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

            self._top.grab_release()
            super().back()
            # for idctrl in self._idctrl_list:
            for idctrl, ctrl in self._idctrl_dict.items(): 
                self._app.delete_control(idctrl)
            # po("subctrl have been deleted!")
            # self._idctrl_list.clear()
            self._idctrl_dict.clear()
            self._top.destroy()
            self._top = None
        self._alive = False
        if self._owner is not None:
            self._owner.back(False)
        super().destroy()

_T_contra = TypeVar("_T_contra", contravariant=True)
class SupportsWrite(Protocol[_T_contra]):
    """自定义协议：表示支持 write(str) 方法的对象"""
    def write(self, s: str) -> Any: ...


class tkWin(WinBasic):
    def __init__(self, cur_path: str, xmlfile: str):
        super().__init__(xmlfile)
        self._is_debug: bool = False
        self._win: tk.Tk = tk.Tk()

        if IS_WINDOWS:
            try:  # >= win 8.1
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:  # win 8.0 or less
                ctypes.windll.user32.SetProcessDPIAware()
            # ctypes.windll.shcore.SetProcessDpiAwareness(1)
            scale_fact = cast(float, ctypes.windll.shcore.GetScaleFactorForDevice(0))
            pv(scale_fact)
            self._win.tk.call("tk", "scaling", scale_fact / 90)

        exit_window = partial(self.exit)
        self._win.protocol("WM_DELETE_WINDOW", exit_window)
        # 注册（绑定）窗口变动事件
        _ = self._win.bind('<Configure>', self._on_winresize)
        _ = self._win.bind_all("<KeyPress>", self._on_keypress)
        _ = self._win.bind_all("<MouseWheel>", self._on_mousewheel)
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

    @property
    def win(self):
        return self._win

    @property
    def path(self):
        return self._cur_path

    # @property
    # def mousepos(self):
        # return self._mousex, self._mousey

    # def _motion(self, event):
        # self._mousex = event.x
        # self._mousey = event.y
        # pv(self._mousex)

    # def _mouseclicked(self, event):
        # self._mousex, self._mousey = event.widget.winfo_pointerxy()

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

        self._xx = cen_x
        self._yy = cen_y
        # super().move_window(self._xx, self._yy)

        # pv(self.pos)

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
            _ = self.create_controls(self._win, frm)

    """
    def _handler_buttonclicked(self, idbutton: str):
        x = self._mousex + self._win.winfo_x()
        # x = self._mousex + self._win.winfo_rootx()
        y = self._mousey + self._win.winfo_y()
        # y = self._mousey + self._win.winfo_rooty()

        # self.process_message(idbutton, mousepos=(x, y))
        self.process_message(idbutton, mousepos=self.mousepos)
    """

    @override
    def create_control(self, parent: object, ctrl_cfg: et.Element,
            level: int = 0, owner: Dialog | None = None) -> tuple[str, object]:
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

        master = cast(tk.Misc, parent)
        parent = cast(tk.Widget, parent)

        match tag:
            case "LabelFrame":
                assert text is not None
                ctrl = ttk.LabelFrame(master, text=text, **options)
                self.debug_print()
            case "Frame" | "Tab":
                if type(parent) is ScrollableFrameCtrl:
                    master = parent.control
                ctrl = tk.Frame(master, **options)
                # ctrl = FrameCtrl(parent, idctrl, **options)
                self.debug_print()
            case "ScrollableFrame":
                ctrl = ScrollableFrameCtrl(parent, self, idctrl,
                    int(attr_dict["Width"]), int(attr_dict["Height"]),
                    **options)
                self.debug_print()
            case "Label":
                assert text is not None
                clickable = attr_dict.get("clickable", False)
                ctrl = LabelCtrl(parent, owner, idctrl, text, clickable, **options)
            case "Button":
                assert text is not None
                ctrl = ButtonCtrl(parent, owner, idctrl, text, **options)
            case "Canvas":
                ctrl = tk.Canvas(parent, **options)
            case "Combobox":
                ctrl = ComboboxCtrl(parent, owner,
                    idself=idctrl,
                    default=int(attr_dict["default"]),
                    **options)
            case "Entry":
                ctrl = EntryCtrl(parent, **options)
            case "ImageButton":
                ctrl = ImageBtttonCtrl(parent, owner, idctrl,
                    respath=self._res_path, imagefile=attr_dict["image"],
                    text=text, **options)
            case "ImagePanel":
                image = attr_dict.get("image", "")
                if image:
                    image = os.path.join(self._res_path, image)
                ctrl = ImagePanelCtrl(parent, idctrl, image, **options)
            case "MatPlot":
                assert text is not None
                if "size" in attr_dict:
                    size = cast(tuple[float, float], literal_eval(attr_dict["size"]))
                    ctrl = MatPlotCtrl(parent, idctrl, text, attr_dict["xLabel"],
                        attr_dict["yLabel"], size)
                else:
                    ctrl = MatPlotCtrl(parent, idctrl, text, attr_dict["xLabel"],
                        attr_dict["yLabel"])
            case "Menu":
                self.debug_print()
                ctrl = self.create_menu(ctrl_cfg, **options)
                _ = self._win.config(menu=ctrl)
            case "RadiobuttonGroup":
                assert text is not None
                ctrl = RadioButtonGroupCtrl(parent, self, owner, idctrl,
                    text=text, subctrlcfg=ctrl_cfg,
                    level=level, **options)
                self.debug_print()
            case "Radiobutton":
                assert text is not None
                if "var" in attr_dict:
                    var_text = attr_dict["var"]
                else:
                    var_text = attr_dict["text"].replace(" ", "").replace(".", "_").replace("\n", "_")
                val = int(attr_dict["value"])
                ctrl = RadioButtonCtrl(parent, owner, idctrl,
                    text=text, vartext=var_text, value=val, **options)
            case "Checkbutton":
                assert text is not None
                if "var" in attr_dict:
                    vartext = attr_dict["var"]
                else:
                    vartext = attr_dict["text"].replace(" ", "").replace(".", "_").replace("\n", "_")
                sel = literal_eval(attr_dict.get("select", "False"))
                ctrl = CheckButtonCtrl(parent, self, idctrl,
                    text=text, vartext=vartext, select=sel, **options)
            case "Statusbar":
                ctrl = MultiStatusBar(parent, **options)
                # for subctrl_cfg in list(ctrl_cfg):
                    # ctrl.set_label(**subctrl_cfg.attrib)
            case "ScrolledText":
                ctrl = scrolledtext.ScrolledText(parent, **options)
            case "Spinbox":
                ctrl = tk.Spinbox(parent,
                    command=lambda: self.process_message(idctrl, event="Changed"),
                    **options)
            case "Style":
                ctrl = ttk.Style()
                ctrl.configure(text, **options)
            case "Toolbar":
                ctrl = ToolbarCtrl(parent, self, self._res_path,
                    list(ctrl_cfg), **options)
                self.debug_print()
            case "Scrollbar":
                ctrl = tk.Scrollbar(parent)
                ctrl.configure(**options)
            case "Listbox":
                ctrl = ListboxCtrl(parent, idctrl, **options)  
            case "PicsListview":
                ctrl = PicsListviewCtrl(parent, self, owner, idctrl,
                    int(attr_dict["num_column"]), int(attr_dict["pic_size"]),
                    self._res_path)
            case "Dialog":
                ctrl = DialogCtrl(parent, self, idctrl, title=text,
                    width=int(attr_dict["Width"]), height=int(attr_dict["Height"]),
                    subctrlcfg_list=list(ctrl_cfg), **options)
                self.debug_print()
            case "Notebook":
                ctrl = NotebookCtrl(parent, self, idctrl,
                    subctrlcfg_list=list(ctrl_cfg), level=level, **options)
            case _:
                raise ValueError(f"{tag}: unknown Control")

        if "tooltip" in attr_dict:
            if tag in ["ImageButton", "Button", "Entry", "Combobox"]:
                Hovertip(ctrl.control, attr_dict["tooltip"], hover_delay=500)
            else:
                Hovertip(ctrl, attr_dict["tooltip"], hover_delay=500)

        self._idctrl_dict[idctrl] = ctrl

        return idctrl, ctrl

    @override
    def assemble_control(self, ctrl: object, attr_dict: dict[str, str], prefix: str = ""):
        ctrl_: tk.Widget = cast(tk.Widget, ctrl)
        if "layout" in attr_dict:
            if attr_dict["layout"] == "pack":
                ctrl_.pack(**(literal_eval(attr_dict["pack"])))
            elif attr_dict["layout"] == "grid":
                ctrl_.grid(**(literal_eval(attr_dict["grid"])))
            elif attr_dict["layout"] == "place":
                ctrl_.place(**(literal_eval(attr_dict["place"])))
            else:
                self.debug_print(f"{prefix}, unknown layout of {attr_dict['layout']}")
                return
        else:
            # self._debug_print(f"{attr_dict['text']}: no assemble")
            return

        if "childOpt" in attr_dict:
            for child in ctrl.winfo_children():
                child.grid_configure(**(literal_eval(attr_dict["childOpt"])))

        self.debug_print(f"{prefix}, layout: {attr_dict['layout']}")

    def create_menu(self, rootcfg: et.Element, **kwargs) -> tk.Menu:
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

    def _on_mousewheel(self, event: tk.Event[tk.Misc]):
        self.process_message("MouseWheel",
            mousepos=(event.x_root, event.y_root), delta=event.delta)

    def exit(self, **kwargs):
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

        @override
        def process_message(self, idmsg: str, **kwargs):
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
                    check_btn = cast(CheckButtonCtrl, self.get_control("屈于现实"))
                    if int(kwargs["val"]) == 1:
                        check_btn.disable()
                    else:
                        check_btn.enable()
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
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True


    filepath = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        filepath = os.path.dirname(os.path.abspath(sys.executable))
    winsample_xml = os.path.join(filepath, "resources", "windowSample.xml")
    eapp = ExampleApp(filepath, winsample_xml)
    eapp.go()
