# !/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
import platform
import ctypes
from functools import partial
from typing import Literal, override, cast
from typing import Any
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
    from matplot import MatPlotCtrl
    from winbasic import EventHanlder, Control, MsgLoop, WinBasic       # guibasic2
except ImportError:
    from pyutilities.logit import pv, pe, po
    from pyutilities.matplot import MatPlotCtrl
    from pyutilities.winbasic import EventHanlder, Control, MsgLoop, WinBasic


__version__ = "4.0.0"
IS_WINDOWS = platform.system() == "Windows"


class tkControl(Control):
    def __init__(self, parent: tk.Widget):
        super().__init__()
        self._tkctrl: tk.Widget = parent
        self._assemble_type: str = "grid"

    @property
    def control(self):
        return self._tkctrl

    @property
    def visible(self):
        return self._tkctrl.winfo_viewable()

    @override
    def configure(self, **kwargs):
        self._tkctrl.configure(**kwargs)

    def grid(self, **options):
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

    def pack(self, **options):
        self._tkctrl.pack(**options)
        self._assemble_type = "pack"

    def place(self, **options):
        self._tkctrl.place(**options)
        self._assemble_type = "place"

    def bind(self, *args, **kwargs):
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


class LabelCtrl(tkControl):
    def __init__(self, parent: tk.Widget, **options):
        super().__init__(parent)
        self._tkctrl = ttk.Label(parent, **options)


class EntryCtrl(ttk.Entry):
    def __init__(self, parent: tk.Misc, **options):
        super().__init__(parent)
        self._var: tk.StringVar = tk.StringVar()
        _= self.configure(textvariable=self._var, **options)

    def get_val(self) -> str:
        return self._var.get()

    def set_val(self, val: str):
        self._var.set(val)


class ImagePanelCtrl(tk.Label):
    # def __init__(self, parent: tk.Misc, imagefile: str = "", **options: int):
    def __init__(self, parent: tk.Misc, imagefile: str,
            width: int, height: int, **options):
        self._parent: tk.Misc = parent
        # tk.Label.__init__(self, parent)
        super().__init__(self._parent)
        if imagefile:
            # img: tk.Image = self.read_image(img_file, options["width"], options["height"])
            img: tk.Image = self.read_image(imagefile, width, height)
            _ = self.configure(text="", image=img, anchor=tk.CENTER, **options)
            self.image = img
        else:
            _ = self.configure(text="", anchor=tk.CENTER, **options)

    def read_image(self, imgfile: str, w: int, h: int)-> tk.Image:
        img1 = PIL.Image.open(imgfile)
        img2 = img1.resize((w, h))
        eimg = PIL.ImageTk.PhotoImage(img2)
        return eimg

    def display_image(self, img: cv2.typing.MatLike):
        # OpenCV represents images in BGR order however PIL represents
        # images in RGB order, so we need to swap the channels
        image1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # convert the images to PIL format...
        image2 = PIL.Image.fromarray(image1)
        # ...and then to ImageTk format
        image3: tk.Image = PIL.ImageTk.PhotoImage(image2)

        _ = self.configure(image=image3)
        self.image = image3


class ImageBtttonCtrl(tk.Button):
    def __init__(self, parent: tk.Misc, app: WinBasic, *,
            imagefile: str, width: int, height: int,
            cmd, text: str | None = None, **options):
        super().__init__(parent)
        self._ww: int = width
        self._hh: int = height
        self._app: WinBasic = app
        # self._ww = self._hh
        eimg = self._read_image(imagefile)
        if not eimg:
            raise RuntimeError(f"fail to read image: {imagefile}")
        if text is not None:
            _ = self.configure(text=text, image=eimg, command=cmd, compound=tk.LEFT,
                relief=tk.FLAT, **options)
        else:
            _ = self.configure(image=eimg, command=cmd, relief=tk.FLAT, **options)
        self.image: tk.Image = eimg

    def _read_image(self, img_file: str) -> tk.Image | None:
        '''
        def _read_image2(self, img_file: str, w: int, h: int):
            # Creating a photoimage object to use image
            photo = tk.PhotoImage(file=img_file)

            # Resizing image to fit on button
            photoimage = photo.subsample(w, h)

            return photoimage
        '''
        eimg: tk.Image | None = None
        # eimg = PIL.ImageTk.PhotoImage(img)
        img = PIL.Image.open(img_file)
        if self._ww:
            img = img.resize((self._ww, self._hh))
        eimg = cast(tk.Image, PIL.ImageTk.PhotoImage(img))
        return eimg

    # TODO: wait to test
    def change_image(self, img_file: str):
        eimg = self._read_image(img_file)
        if eimg:
            _ = self.configure(image=eimg)


class CheckbuttonCtrl(tk.Checkbutton):
    def __init__(self, parent: tk.Misc, app: WinBasic, idself: str, *,
            text: str, select: Literal["0", "1"], **options):
        super().__init__(parent)
        self._var: tk.IntVar = tk.IntVar()
        _ = self.configure(text=text,
            variable=self._var, **options)

        # trace_add(self, mode: Literal["array", "read", "write", "unset"],
            # callback: Callable[[str, str, str], object])
        _ = self._var.trace_add("write",
            lambda u0, u1, u2: app.process_message(idself, event="Changed", val=self._var.get()))

        if select == "1":
            super().select()

    def get_val(self) -> int:
        return self._var.get()


class ComboboxCtrl(ttk.Combobox):
    def __init__(self, parent: tk.Misc, app: WinBasic, *,
            idself: str, default: int, **options):
        super().__init__(parent)
        self._var: tk.StringVar = tk.StringVar()
        _ = self.configure(textvariable=self._var, **options)
        _ = self.current(default)
        _ = self.bind(
            "<<ComboboxSelected>>",
            lambda event: app.process_message(
                idself, event="Selected", val=self._var.get()
            ),
        )

    def get_val(self) -> str:
        return self._var.get()

    def set_val(self, val: str):
        self._var.set(val)


class RadiobuttonGroupCtrl(ttk.LabelFrame):
    def __init__(self, parent: tk.Misc, app: WinBasic, *,
            idself: str, text: str,
            subctrlcfg: et.Element, level: int, **options):
        super().__init__(parent)
        self._idself: str = idself
        self._var_val: tk.IntVar = tk.IntVar()
        self._app: WinBasic = app
        # pv(options)
        _ = self.configure(text=text, **options)
        self._radbuttons_lst: list[ttk.Radiobutton] = []
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
                command=lambda: self._app.process_message(
                    self._idself, event="Changed", val=self.get_val()))
            print(f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
            self._app.assemble_control(sub_ctrl, radbtn_attr_dict)

    def _add_radiobutton(self, **opt_dict):
        radbutton = ttk.Radiobutton(master=self, variable=self._var_val, **opt_dict)
        # create_control(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> tuple[str, tk.Misc]:
        self._radbuttons_lst.append(radbutton)
        return radbutton

    @override
    def destroy(self):
        po("RadiobuttonGroupCtrl destroy")
        for radbutton in self._radbuttons_lst:
            # print(f"going to del {id_ctrl}")
            radbutton.destroy()
        self._radbuttons_lst.clear()
        super().destroy()


class PicsListviewCtrl(tkControl):
    def __init__(self, parent: tkControl, idself: str,
            num_column: int, pic_size: int, res_path: str):
        tkControl.__init__(self, parent)
        self._tkctrl: ttk.Frame = ttk.Frame(parent.control)
        self._imagepanelctrl_list: list[ImagePanelCtrl] = []
        self._parent: tkControl = parent
        self._idself: str = idself
        self._num_column: int = num_column
        self._pic_size: int = pic_size
        self._res_path: str = res_path

    def display_images(self, imagefile_list: list[str]):
        spacing = int(self._pic_size/10)
        for i, imagefile in enumerate(imagefile_list):
            imagfile = os.path.join(self._res_path, imagefile)
            image_panel = ImagePanelCtrl(self._tkctrl, imagefile,
                width=self._pic_size, height=self._pic_size)
            image_panel.grid(row=i // self._num_column, column=i % self._num_column,
                padx=spacing, pady=spacing)
            _= image_panel.bind("<Button-1>", lambda e, idx=i: self.highlight_image(index=idx))
            self._imagepanelctrl_list.append(image_panel)

    def highlight_image(self, index: int):
        for i, image_panel in enumerate(self._imagepanelctrl_list):
            if i == index:
                _ = image_panel.configure(highlightbackground="blue", highlightthickness=2)
                self._parent.process_message(self._idself, event="clicked", index=i)
            else:
                _ = image_panel.configure(highlightthickness=0)

    @override
    def destroy(self):
        self._imagepanelctrl_list.clear()
        super().destroy()


class ToolbarCtrl(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: WinBasic, res_path: str,
            subctrls: list[et.Element], **options):
        self._parent: tk.Misc = parent
        super().__init__(self._parent, **options)
        self._res_path: str = res_path
        # self._tooltip = tix.Balloon(root)
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


class NotebookCtrl(ttk.Notebook):
    def __init__(self, parent: tk.Misc, app: WinBasic, *,
            subctrlcfg_list: list[et.Element], level: int, **options):
        super().__init__(parent, **options)
        print()
        self._app: WinBasic = app
        self._idctrl_list: list[str] = []
        for subctrl_cfg in list(subctrlcfg_list):
            cid, sub_ctrl = self._app.create_control(self,
                subctrl_cfg, level + 1)
            self._idctrl_list.append(cid)
            print(f"tabCtrl: {subctrl_cfg.tag}")
            self.add(cast(tk.Widget, sub_ctrl),
                text=subctrl_cfg.attrib["text"])
            for item in list(subctrl_cfg):
                idctrl_list = self._app.create_controls(sub_ctrl, item,
                    level + 2)
                self._idctrl_list.extend(idctrl_list)

    @override
    def destroy(self):
        po("NotebookCtrl destroy")
        for idctrl in self._idctrl_list:
            self._app.delete_control(idctrl)
        self._idctrl_list.clear()
        super().destroy()


class FrameCtrl(tkControl):
    def __init__(self, parent, **options):
        tkControl.__init__(self, parent, **options)
        # MsgLoop.__init__(self)
        self._tkctrl: ttk.Frame = ttk.Frame(parent, **options)
        self._parent = parent


class DialogCtrl(tkControl, MsgLoop):
    def __init__(self, parent: tk.Widget, app: WinBasic, *,
            idself: str, title: str,
            subctrlcfg_list: list[et.Element], **options):
        self._parent: tk.Misc = parent
        self._owner: MsgLoop | None = None
        tkControl.__init__(self, self._parent)
        MsgLoop.__init__(self)
        self._top: tk.Toplevel | None = None
        self._app: WinBasic = app
        self._title: str = title
        self._alive: bool = False
        self._idself: str = idself
        self._subctrlcfg_list: list[et.Element] = subctrlcfg_list
        self._confirm: bool = False
        # self._confirm_handler: EventHanlder | None = None
        self._idctrl_list: list[str] = []

    @property
    def owner(self):
        return self._owner

    @property
    def alive(self):
        return self._alive

    def do_show(self, owner: MsgLoop | None = None):
        print(f"show Dialog {self._title}")
        # self.deiconify()
        self._alive = True
        if owner is not None:
            self._owner = owner

        self._top = tk.Toplevel(self._parent)
        self._top.title(self._title)
        # x, y, _, _ = self._app.get_winsize()
        x = self._parent.winfo_rootx()
        y = self._parent.winfo_rooty()
        # place dialog below parent if running htest
        self._top.geometry("+%d+%d" % (x+30, y+30))
        _ = self._top.resizable(None, None)
        self._top.protocol("WM_DELETE_WINDOW", self.destroy) # intercept close button

        # self.resizable(0, 0)        # 禁止调节大小
        # self.withdraw()
        # id_ctrl = self._title.replace(" ", "").replace(".", "_").replace("\n", "_")
        iddlg = self._idself

        frm_dlg_xml = self._app.create_xml("Top", {})

        frm_main_xml = self._app.create_xml("Frame", {"id": f"frmMain{iddlg}"}, frm_dlg_xml)
        id_frmain, frm_main = self._app.create_control(self._top,
            frm_main_xml, 0)
        self._idctrl_list.append(id_frmain)

        for sub_ctrl in self._subctrlcfg_list:
            subidctrl_list = self._app.create_controls(frm_main, sub_ctrl, 1)
            self._idctrl_list.extend(subidctrl_list)

        _ = self._app.assemble_control(frm_main, {"layout": "pack",
            "pack": "{'side':'top','fill':'both','expand':True,'padx':5,'pady':5}"})

        frmbot_xml = self._app.create_xml("Frame", {"id": f"frmBot{iddlg}"}, frm_dlg_xml)
        id_frmbot, frm_bot = self._app.create_control(self._top,
            frmbot_xml, 0)
        self._idctrl_list.append(id_frmbot)

        xml = self._app.create_xml("Button", {"id": f"btnConfirm{iddlg}",
            "text": "Confirm", "options": "{'width':20}"}, frmbot_xml)
        idctrl, ctrl = self._app.create_control(frm_bot, xml, 1)
        self._idctrl_list.append(idctrl)
        _ = self._app.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")

        xml = self._app.create_xml("Button", {"id": f"btnCancel{iddlg}",
            "text": "Cancel", "options": "{'width':20}"}, frmbot_xml)
        idctrl, ctrl = self._app.create_control(frm_bot, xml, 1)
        self._idctrl_list.append(idctrl)
        # pv(self._idctrl_list)
        _ = self._app.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")

        _ = self._app.assemble_control(frm_bot, {"layout": "pack",
            "pack": "{'side':'bottom','fill':'both','expand':True,'padx':5,'pady':5}"})

        for idctrl in self._idctrl_list:
            msg_handler = partial(self.process_message, idctrl)
            self._app.register_eventhandler(idctrl, msg_handler)

        """
        try:
            before_go = getattr(self, "_before_go")  # get before_go from child
            before_go()
        except AttributeError as r:
            po(f"{self._title} Warnning to go: {r}")
        """
        _ = self.process_message("beforego")

        MsgLoop.register_eventhandler(self, "btnCancel" + self._idself, self._do_cancel)
        MsgLoop.register_eventhandler(self, "btnConfirm" + self._idself, self._do_confirm)

        # self._top.wait_visibility() # can't grab until window appears, so we wait
        self._top.transient(self._parent)   # dialog window is related to main
        self._top.grab_set()        # ensure all input goes to our window
        # 设置achieved_value，使该窗口始终处于其他窗口的上层
        self._top.attributes("-topmost", True)
        self._parent.wait_window(self._top)
        # pv(self._id_list)

    def get_control(self, idctrl: str) -> tk.Misc:
        return self._app.get_control(idctrl)

    def _do_cancel(self):
        po(f"Dialog {self._title} _do_cancel")
        self._confirm = False
        self.destroy()

    def _do_confirm(self):
        po(f"Dialog {self._title} _do_confirm")
        self._confirm = True
        self.destroy()

    @override
    def destroy(self):
        # self.withdraw()
        if self._top:
            ret, msg = self.process_message("confirm", confirm=self._confirm)
            if not ret:
                self._app.show_err(self._title, msg)
                return
            try:
                before_close = getattr(
                    self, "_before_close"
                )  # get before_close from child
                ret, msg = before_close(self._confirm)
                if not ret:
                    self._app.show_err(self._title, msg)
                    return
            except AttributeError as r:
                po(f"{self._title} Warnning to exit: {r}")

            self._top.grab_release()
            for idctrl in self._idctrl_list:
                self._app.delete_control(idctrl)
            self._idctrl_list.clear()
            self._top.destroy()
            self._top = None
        self._alive = False
        # super().destroy()


class tkWin(WinBasic):
    def __init__(self, cur_path: str, xmlfile: str):
        super().__init__()
        # MsgLoop.__init__(self)
        self._win: tk.Tk = tk.Tk()

        if IS_WINDOWS:
            try:  # >= win 8.1
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:  # win 8.0 or less
                ctypes.windll.user32.SetProcessDPIAware()
            # ctypes.windll.shcore.SetProcessDpiAwareness(1)
            scale_fact: float = ctypes.windll.shcore.GetScaleFactorForDevice(0)
            self._win.tk.call("tk", "scaling", scale_fact / 90)

        self._win.protocol("WM_DELETE_WINDOW", self.exit_window)
        # self._win.columnconfigure(0, weight=1)
        # self._win.rowconfigure(0, weight=1)

        self._cur_path: str = cur_path

        self._title: str = ""
        self._res_path: str = ""

        self.create_window(xmlfile)

    @property
    def win(self):
        return self._win

    @property
    def path(self):
        return self._cur_path

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
        cen_x = (sw - width) / 2
        cen_y = (sh - hight) / 2

        # 设置窗口大小并居中
        self._win.geometry(f"{int(width)}x{int(hight)}+{int(cen_x)}+{int(cen_y)}")

    @override
    def create_window(self, xmlfile: str):
        self._res_path = os.path.dirname(xmlfile)

        element_tree = et.parse(xmlfile)
        win = element_tree.getroot()
        win_attr = win.attrib

        self._title = win_attr["Title"]
        self._win.title(self._title)

        if "Height" in win_attr:
            self._w = int(win_attr["Width"])
            self._h = int(win_attr["Height"])

            self._center_window(self._w, self._h)

        for frm in list(win):
            _ = self.create_controls(self._win, frm)

    @override
    def get_winsize(self) -> tuple[int, int, int, int]:
        '''
            return x, y, w, h
        '''
        return self._win.winfo_rootx(), self._win.winfo_rooty(), self._w, self._h

    @override
    def create_control(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> tuple[str, tk.Misc]:
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
        print(f"{'  '*level}{tag}, id: {idctrl}, text: {text}", end="")

        if idctrl in self._idctrl_dict:
            raise KeyError(f"{idctrl} already exists")

        options: dict[str, Any] = {}
        if "options" in attr_dict:
            options = eval(attr_dict["options"])

        match tag:
            case "LabelFrame":
                assert text is not None
                ctrl = ttk.LabelFrame(parent, text=text, **options)
                print()
            case "Frame" | "Tab":
                # ctrl = ttk.Frame(parent, **options)
                ctrl = tk.Frame(parent, **options)
                print()
            case "Label":
                assert text is not None
                # ctrl = ttk.Label(parent, text=text, **options)
                ctrl = LabelCtrl(parent, text=text, **options)
                clickable = attr_dict.get("clickable", False)
                if clickable:
                    print(f"{idctrl} clickable")
                    _= ctrl.bind("<Button-1>",
                        lambda event: self.process_message(idctrl, event="Clicked"))
            case "Button":
                assert text is not None
                ctrl = ttk.Button(parent, text=text,
                    command=lambda: self.process_message(idctrl, event="Clicked"),
                        **options)
            case "Canvas":
                ctrl = tk.Canvas(parent, **options)
            case "Combobox":
                ctrl = ComboboxCtrl(parent, app=self,
                    idself=idctrl,
                    default=int(attr_dict["default"]),
                    **options)
            case "Entry":
                ctrl = EntryCtrl(parent, **options)
            case "ImageButton":
                ctrl = ImageBtttonCtrl(parent, app=self,
                    imagefile=os.path.join(self._res_path, attr_dict["img"]),
                    text=text,
                    cmd=lambda: self.process_message(idctrl, event="Clicked"),
                    **options)
            case "ImagePanel":
                img = attr_dict.get("img", "")
                if img:
                    img = os.path.join(self._res_path, img)
                ctrl = ImagePanelCtrl(parent, img, **options)
            case "MatPlot":
                assert text is not None
                if "size" in attr_dict:
                    size = cast(tuple[float, float], literal_eval(attr_dict["size"]))
                    ctrl = MatPlotCtrl(parent, text, attr_dict["xLabel"],
                        attr_dict["yLabel"], size)
                else:
                    ctrl = MatPlotCtrl(parent, text, attr_dict["xLabel"],
                        attr_dict["yLabel"])
            case "Menu":
                print()
                ctrl = self.create_menu(ctrl_cfg, **options)
                _ = self._win.config(menu=ctrl)
            case "RadiobuttonGroup":
                assert text is not None
                ctrl = RadiobuttonGroupCtrl(parent, self, idself=idctrl,
                    text=text, subctrlcfg=ctrl_cfg,
                    level=level, **options)
                print()
            case "Radiobutton":
                assert text is not None
                if "var" in attr_dict:
                    var_text = attr_dict["var"]
                else:
                    var_text = attr_dict["text"].replace(" ", "").replace(".", "_").replace("\n", "_")
                var_text_name = f"_{var_text}"
                if var_text_name not in self.__dict__:
                    self.__dict__[var_text_name] = tk.IntVar()
                variable = self.__dict__[var_text_name]
                idctrl = var_text
                # print(f", title = {title}", end="")
                ctrl = ttk.Radiobutton(parent, variable=variable,
                    value=int(attr_dict["value"]), text=text,
                    command=lambda: self.process_message(idctrl,
                        event="Changed", val=variable.get()),
                    **options)
            case "Checkbutton":
                assert text is not None
                if "var" in attr_dict:
                    var_text = attr_dict["var"]
                else:
                    var_text = attr_dict["text"].replace(" ", "").replace(".", "_").replace("\n", "_")
                var_text_name = f"_{var_text}"
                # pv(var_text_name)
                if var_text_name not in self.__dict__:
                    self.__dict__[var_text_name] = tk.IntVar()
                variable: tk.IntVar = self.__dict__[var_text_name]
                ctrl = tk.Checkbutton(parent, text=text,
                    variable=variable, **options)

                # trace_add(self, mode: Literal["array", "read", "write", "unset"],
                    # callback: Callable[[str, str, str], object])
                _ = variable.trace_add("write",
                    lambda u0, u1, u2: self.process_message(idctrl, event="Changed", val=variable.get()))

                select = attr_dict.get("select", "0")
                if select == "1":
                    ctrl.select()
            case "Statusbar":
                ctrl = MultiStatusBar(parent, **options)
                for subctrl_cfg in list(ctrl_cfg):
                    ctrl.set_label(**subctrl_cfg.attrib)
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
                print()
            case "Scrollbar":
                ctrl = tk.Scrollbar(parent)
                ctrl.configure(**options)
            case "Listbox":
                ctrl = tk.Listbox(parent)
                ctrl.configure(**options)
            case "PicsListview":
                ctrl = PicsListviewCtrl(parent, idctrl, int(attr_dict["num_column"]),
                    int(attr_dict["pic_size"]), self._res_path)
            case "Dialog":
                ctrl = DialogCtrl(parent, self, idself=idctrl, title=text,
                    subctrlcfg_list=list(ctrl_cfg), **options)
                print()
            case "Notebook":
                ctrl = NotebookCtrl(parent, self,
                    subctrlcfg_list=list(ctrl_cfg), level=level, **options)
            case _:
                raise ValueError(f"{tag}: unknown Control")

        if "tooltip" in attr_dict:
            Hovertip(ctrl, attr_dict["tooltip"], hover_delay=500)

        self._idctrl_dict[idctrl] = ctrl
        return idctrl, ctrl

    @override
    def assemble_control(self, ctrl: tk.Misc, attr_dict: dict[str, str], prefix: str = ""):
        ctrl_: tk.Widget = cast(tk.Widget, ctrl)
        if "layout" in attr_dict:
            if attr_dict["layout"] == "pack":
                ctrl_.pack(**(literal_eval(attr_dict["pack"])))
            elif attr_dict["layout"] == "grid":
                ctrl_.grid(**(literal_eval(attr_dict["grid"])))
            elif attr_dict["layout"] == "place":
                ctrl_.place(**(literal_eval(attr_dict["place"])))
            else:
                print(f"{prefix}, unknown layout of {attr_dict['layout']}")
                return
        else:
            # print(f"{atrDict['text']}: no assemble")
            return

        if "childOpt" in attr_dict:
            for child in ctrl.winfo_children():
                child.grid_configure(**(literal_eval(attr_dict["childOpt"])))

        print(f"{prefix}, layout: {attr_dict['layout']}")

    def create_menu(self, rootcfg: et.Element, **kwargs) -> tk.Menu:
        menubar = tk.Menu(self._win, **kwargs)

        # def get_cmd(cmd_name, msg, ext_msg=""):
        def get_cmd(cmd_name, **kwargs):
            # return lambda: self.process_message(cmd_name, msg, ext_msg)
            return lambda: self.process_message(cmd_name, **kwargs)

        # def get_cmd_e(cmd_name, msg, ext_msg=""):
        def get_cmd_e(cmd_name, **kwargs):
            # return lambda event: self.process_message(cmd_name, msg, ext_msg)
            return lambda event: self.process_message(cmd_name, **kwargs)

        for menucfg in list(rootcfg):
            attr_dict = menucfg.attrib
            label = attr_dict["Header"]
            print(f"  Menu: {label}")
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
                    print(f"    subMenu: {submenucfg.tag}")
                    continue
                if "options" in subattr_dict:
                    sub_options = literal_eval(subattr_dict["options"])
                else:
                    sub_options = {}
                sub_label = subattr_dict["Command"]
                cmd_name = str(sub_label.replace(" ", "").replace("...", ""))
                print(f"    subMenu: {tag} -> {sub_label}")
                if tag == "Checkbutton":
                    var_name = subattr_dict["variable"]
                    self.__dict__[f"_{var_name}"] = tk.BooleanVar()
                    var = self.__dict__[f"_{var_name}"]
                    # var.set(True)
                    # msg = "Changed"
                    # ext_msg = var.get()
                    # cmd = get_cmd(cmd_name, msg, ext_msg)
                    kwargs = {"event": "Changed", "val": var.get()}
                    cmd = get_cmd(cmd_name, **kwargs)
                    menu.add_checkbutton(
                        label=sub_label, command=cmd, variable=var, **sub_options
                    )
                elif tag == "MenuItem":
                    # msg = "Clicked"
                    # ext_msg = ""
                    kwargs = {"event": "Clicked"}
                    # cmd = get_cmd(cmd_name, msg, ext_msg)
                    cmd = get_cmd(cmd_name, **kwargs)
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
                    cmd = get_cmd_e(cmd_name, **kwargs)
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
        try:
            before_go = getattr(self, "_before_go")  # get before_go from child
            before_go()
        except AttributeError as r:
            print(f"Warnning to go: {r}")

        MsgLoop.register_eventhandler(self, "Exit", self.exit_window)
        MsgLoop.register_eventhandler(self, "Quit", self.exit_window)

        self._win.mainloop()

    def exit_window(self):
        res = tkMessageBox.askquestion(
            "Exit Application", "Do you really want to exit?"
        )
        if res == "yes":
            try:
                before_close = getattr(
                    self, "_before_close"
                )  # get before_close from child
                before_close()
            except AttributeError as r:
                print(f"Warnning to exit: {r}")
            self._win.destroy()


if __name__ == "__main__":
    class ExampleApp(tkWin):
        # def process_message(self, id_ctrl, *args, **kwargs):
        @override
        def process_message(self, idmsg: str, **kwargs):
            match idmsg:
                case "InfoBox":
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
                    values = ["富强民主", "文明和谐", "自由平等","公正法治","爱国敬业","诚信友善"]
                    monty2 = self.get_control("控件示范区2")
                    monty2.configure(text=values[int(kwargs["val"])])
                case "varChkEna":
                    check_btn = self.get_control("遵从内心")
                    if int(kwargs["val"]) == 1:
                        self.disable_control(check_btn)
                    else:
                        self.disable_control(check_btn, False)
                case "varChkUne":
                    check_btn = self.get_control("屈于现实")
                    if int(kwargs["val"]) == 1:
                        self.disable_control(check_btn)
                    else:
                        self.disable_control(check_btn, False)
                case "点击之后_按钮失效":
                    btn = self.get_control("点击之后_按钮失效")
                    name = self.get_control("name")
                    btn.configure(text='Hello\n ' + name.get_val())
                    self.disable_control(btn)
                case "blankSpin":
                    spin = self.get_control("blankSpin")
                    value = spin.get()
                    scr = self.get_control("scrolledtext")
                    scr.insert(tk.INSERT, value + '\n')
                case "bookSpin":
                    spin = self.get_control("bookSpin")
                    value = spin.get()
                    scr = self.get_control("scrolledtext")
                    scr.insert(tk.INSERT, value + '\n')
                case _:
                    # super().process_message(id_ctrl, *args, **kwargs)
                    super().process_message(idmsg, **kwargs)


    filepath = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        filepath = os.path.dirname(os.path.abspath(sys.executable))
    winsample_xml = os.path.join(filepath, "resources", "windowSample.xml")
    eapp = ExampleApp(filepath, winsample_xml)
    # eapp.create_window(winsample_xml)
    eapp.go()
