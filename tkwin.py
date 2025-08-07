#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
import platform
import ctypes
from typing import Any, override
from collections.abc import Callable

import tkinter as tk
import tkinter.messagebox as tkMessageBox
from tkinter import ttk
from tkinter import scrolledtext
import xml.etree.ElementTree as et
from ast import literal_eval

import cv2

try:
    from logit import pv, pe
    from matplot import MatPlot
    from winbasic import EventHanlder, WinBasic
except ImportError:
    from pyutilities.logit import pv, pe
    from pyutilities.matplot import MatPlot
    from pyutilities.winbasic import EventHanlder, WinBasic

from idlelib.statusbar import MultiStatusBar
from idlelib.tooltip import Hovertip

# from PIL import Image, ImageTk    # for imgButton
import PIL

DlgCallback = Callable[[bool], (bool, str)]
# EventCallback = Callable[[tk.Event], object]

__version__ = "3.3.1"
IS_WINDOWS = platform.system() == "Windows"


class Toolbar(tk.Frame):
    def __init__(self, parent: tk.Misc, app: WinBasic, res_path: str, subctrls: list[et.Element]):
        self._parent: tk.Misc = parent
        super().__init__(self._parent)
        self._res_path: str = res_path
        # self._tooltip = tix.Balloon(root)
        # self._create_subctrls(app: WinBasic, subctrls)
        for subctrl in subctrls:
            _ = app.create_controls(self, subctrl, 1)

    # def _create_subctrls(self, app: WinBasic, subctrls):
        # for subctrl_cfg in subctrls:
            # _, sub_ctrl = app.create_control(self, subctrl_cfg)
            # app.assemble_control(sub_ctrl, subctrl_cfg.attrib)


class ImgPanel(tk.Label):
    def __init__(self, parent: tk.Misc, img_file: str = "", **options: int):
        self._parent: tk.Misc = parent
        # tk.Label.__init__(self, parent)
        super().__init__(self._parent)
        if img_file:
            img: tk.Image = self.read_image(img_file, options["width"], options["height"])
            _ = self.configure(text="", image=img, anchor=tk.CENTER)
            self.image = img
        else:
            _ = self.configure(text="", anchor=tk.CENTER)

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


class EntryCtrl(ttk.Entry):
    def __init__(self, parent: tk.Misc, **cfg_dict: Any):
        super().__init__(parent)
        self._var_val: tk.StringVar = tk.StringVar()
        _= self.configure(textvariable=self._var_val, **cfg_dict)

    # @staticmethod
    # def __new__(cls, *args, **kwargs):
        # if cls is EntryCtrl and args and isinstance(args[0], ttk.Entry):
            # return super().__new__(EntryCtrl)
        # else:
            # return super().__new__(cls)

    def get_val(self) -> str:
        return self._var_val.get()

    def set_val(self, val: str):
        self._var_val.set(val)


class ComboboxCtrl(ttk.Combobox):
    def __init__(self, parent: tk.Misc, **cfg_dict: Any):
        super().__init__(parent)
        self._var_val: tk.StringVar = tk.StringVar()
        app: WinBasic = cfg_dict["app"]
        _ = self.configure(textvariable=self._var_val, **cfg_dict["options"])
        _ = self.current(cfg_dict["default"])
        _ = self.bind(
            "<<ComboboxSelected>>",
            lambda event: app.process_message(
                cfg_dict["id_ctrl"], "Selected", self._var_val.get()
            ),
        )

    def get_val(self) -> str:
        return self._var_val.get()

    def set_val(self, val: str):
        self._var_val.set(val)


class RadiobuttonCtrl(ttk.LabelFrame):
    def __init__(self, id_ctrl: str, parent: tk.Misc, **cfg_dict: Any):
        super().__init__(parent)
        # Control.__init__(self, "int")
        self._id_ctrl: str = id_ctrl
        self._var_val: tk.IntVar = tk.IntVar()
        self._app: WinBasic = cfg_dict["app"]
        _ = self.configure(text=cfg_dict["text"], **cfg_dict["options"])
        self._radbuttons_lst: list[ttk.Radiobutton] = []
        _ = self._create_subctrls(cfg_dict["subctrls"],
            cfg_dict["level"])

    def get_val(self) -> int:
        return self._var_val.get()

    def set_val(self, val: int):
        self._var_val.set(val)

    def _create_subctrls(self, subctrls: et.Element, level: int):
        for subctrl_cfg in subctrls:
            radbtn_atr_dict = subctrl_cfg.attrib
            val = int(radbtn_atr_dict["value"])
            text: str = radbtn_atr_dict["text"]
            sub_ctrl = self._add_radiobutton(value=val, text=text,
                command=lambda: self._app.process_message(
                    self._id_ctrl, "Changed", self.get_val()))
            print(
                f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
            self._app.assemble_control(sub_ctrl, radbtn_atr_dict)

    def _add_radiobutton(self, **opt_dict: Any):
        radbutton = ttk.Radiobutton(master=self, variable=self._var_val, **opt_dict)
        # create_control(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> tuple[str, tk.Misc]:
        self._radbuttons_lst.append(radbutton)
        return radbutton


class ImgBtnCtrl(tk.Button):
    _ww: int = 0
    _hh: int = 0
    def __init__(self, parent: tk.Misc, **cfg_dict: Any):
        super().__init__(parent)
        # Control.__init__(self)
        self._app: WinBasic = cfg_dict["app"]
        img_file: str = cfg_dict["img_file"]
        options: dict[str, Any] = cfg_dict["options"]
        # pv(options)
        cmd = cfg_dict["command"]
        self._hh = options.get("height", 0)
        # pv(cfg_dict["options"])
        self._ww = self._hh
        eimg = self._read_image(img_file)
        text: str = cfg_dict.get("text", "")
        # pv(text)
        if text:
            _ = self.configure(
                text=text, image=eimg, command=cmd, compound=tk.LEFT,
                relief=tk.FLAT, **options
            )
        else:
            _ = self.configure(image=eimg, command=cmd, relief=tk.FLAT,
                **options)
        self.image = eimg

    def _read_image(self, img_file: str):
        '''
        def _read_image2(self, img_file: str, w: int, h: int):
            # Creating a photoimage object to use image
            photo = tk.PhotoImage(file=img_file)

            # Resizing image to fit on button
            photoimage = photo.subsample(w, h)

            return photoimage
        '''
        # eimg = PIL.ImageTk.PhotoImage(img)
        img = PIL.Image.open(img_file)
        if self._ww:
            img = img.resize((self._ww, self._hh))
        eimg = PIL.ImageTk.PhotoImage(img)
        return eimg

    # TODO: wait to test
    def change_image(self, img_file: str):
        eimg = self._read_image(img_file)
        _ = self.configure(image=eimg)


class Dialog(ttk.Frame):
    _confirm: bool = False
    _confirm_handler: EventHanlder | None = None
    _beforego_callback: EventHanlder | None = None
    _id_list: list[str] = []

    def __init__(self, parent: tk.Misc, app: WinBasic, title: str, subctrlcfg_list: list[et.Element], **options: Any) -> None:
        super().__init__(app.win, **options)
        self._top: tk.Toplevel | None = None
        self._parent: tk.Misc = parent
        self._app: WinBasic = app
        self._title: str = title
        self._subctrlcfg_list: list[et.Element] = subctrlcfg_list
        # self._options = options

    def do_show(self):
        # self.deiconify()
        self._top = tk.Toplevel(self._parent)
        self._top.title(self._title)
        # win = self._app.win
        x, y, _, _ = self._app.get_winsize()
        # place dialog below parent if running htest
        self._top.geometry("+%d+%d" % (x+30, y+30))
        _ = self._top.resizable(None, None)
        self._top.protocol("WM_DELETE_WINDOW", self.destroy) # intercept close button

        # self.resizable(0, 0)        # 禁止调节大小
        # self.withdraw()
        id_ctrl = self._title.replace(" ", "").replace(".", "_").replace("\n", "_")

        frm_dlg_xml = self._app.create_xml("Top", {})

        frm_main_xml = self._app.create_xml("Frame", {"text": f"frmMain{id_ctrl}"}, frm_dlg_xml)
        id_frmain, frm_main = self._app.create_control(self._top,
            frm_main_xml, 0)
        self._id_list.append(id_frmain)

        for sub_ctrl in self._subctrlcfg_list:
            subid_list = self._app.create_controls(frm_main, sub_ctrl, 1)
            self._id_list.extend(subid_list)

        _ = self._app.assemble_control(frm_main, {"layout": "pack",
            "pack": "{'side':'top','fill':'both','expand':True,'padx':5,'pady':5}"})

        frm_bot_xml = self._app.create_xml("Frame", {"text": f"frmBot{id_ctrl}"}, frm_dlg_xml)
        id_frmbot, frm_bot = self._app.create_control(self._top,
            frm_bot_xml, 0)
        self._id_list.append(id_frmbot)

        xml = self._app.create_xml("Button", {"id": f"btnConfirm{id_ctrl}",
            "text": "Confirm", "options": "{'width':20}"}, frm_bot_xml)
        id_, ctrl = self._app.create_control(frm_bot, xml, 1)
        self._id_list.append(id_)
        _ = self._app.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")
        _ = self._app.register_eventhandler(id_, self._do_confirm)

        xml = self._app.create_xml("Button", {"id": f"btnCancel{id_ctrl}",
            "text": "Cancel", "options": "{'width':20}"}, frm_bot_xml)
        id_, ctrl = self._app.create_control(frm_bot, xml, 1)
        self._id_list.append(id_)
        # pv(self._id_list)
        _ = self._app.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")
        _ = self._app.register_eventhandler(id_, self._do_cancel)

        _ = self._app.assemble_control(frm_bot, {"layout": "pack",
            "pack": "{'side':'bottom','fill':'both','expand':True,'padx':5,'pady':5}"})

        if self._beforego_callback:
            self._beforego_callback()

        # self._top.wait_visibility() # can't grab until window appears, so we wait
        self._top.transient(self._app.win)   # dialog window is related to main
        self._top.grab_set()        # ensure all input goes to our window
        # 设置achieved_value，使该窗口始终处于其他窗口的上层
        self._top.attributes("-topmost", 1)
        self.wait_window(self._top)

    def get_control(self, id_: str) -> tk.Misc:
        return self._app.get_control(id_)

    def _do_cancel(self, *args: Any, **kwargs: Any):
        pv(Any)
        pv(kwargs)
        self._confirm = False
        self.destroy()

    def _do_confirm(self, *args: Any, **kwargs: Any):
        pv(Any)
        pv(kwargs)
        self._confirm = True
        self.destroy()

    def register_callback(self, event: str, callback: EventHanlder):
        match event:
            case "confirm":
                self._confirm_handler = callback
            case "beforego":
                self._beforego_callback = callback
            case _:
                raise NotImplementedError(f"{event}")

    @override
    def destroy(self):
        # self.withdraw()
        if self._top:
            if self._confirm_handler:
                ret, msg = self._confirm_handler(self._confirm)
                if not ret:
                    self._app.show_err(self._title, msg)
                    return
            self._top.grab_release()
            for id_ctrl in self._id_list:
                self._app.delete_control(id_ctrl)
            self._id_list.clear()
            self._top.destroy()
            self._top = None


class MatPlotCtrl(MatPlot, tk.Misc):
    pass


class tkWin(WinBasic):
    def __init__(self, cur_path: str):
        super().__init__()
        # self._win = tk.Tk()

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

        self._ctrls_dict: dict[str, tk.Misc] = {}
        self._eventhandler_dict: dict[str, EventHanlder] = {}
        self._cur_path: str = cur_path

        self._title: str = ""
        self._res_path: str = ""

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
    def create_window(self, cfg_file: str):
        self._res_path = os.path.dirname(cfg_file)

        element_tree = et.parse(cfg_file)
        win = element_tree.getroot()
        win_attr = win.attrib

        self._title = win_attr["Title"]
        self._win.title(self._title)

        if "Height" in win_attr:
            width = int(win_attr["Width"])
            hight = int(win_attr["Height"])

            self._center_window(width, hight)

        for frm in list(win):
            _ = self.create_controls(self._win, frm)

    @override
    def get_winsize(self) -> tuple[int, int, int, int]:
        '''
            return x, y, w, h
        '''
        return self._win.winfo_rootx(), self._win.winfo_rooty(), self._w, self._h

    @override
    def create_controls(self, parent: tk.Misc, ctrls_cfg: et.Element, level: int = 0) -> list[str]:
        id_list: list[str] = []
        id_, ctrl = self.create_control(parent, ctrls_cfg, level)
        id_list.append(id_)
        tag = ctrls_cfg.tag
        if tag in ["Menu", "Notebook", "RadiobuttonGroup",
            "Statusbar", "Toolbar", "Dialog"]:
            pass
        else:
            for sub_cfg in list(ctrls_cfg):
                subid_list = self.create_controls(ctrl, sub_cfg, level + 1)
                id_list.extend(subid_list)
        self.assemble_control(ctrl, ctrls_cfg.attrib, f"{'  '*level}")
        return id_list

    @override
    def assemble_control(self, ctrl: tk.Misc, atr_dict: dict[str, str], prefix: str = ""):
        # assert isinstance(ctrl, tk.Widget)
        ctrl_: tk.Widget = ctrl
        if "layout" in atr_dict:
            if atr_dict["layout"] == "pack":
                ctrl_.pack(**(literal_eval(atr_dict["pack"])))
            elif atr_dict["layout"] == "grid":
                ctrl_.grid(**(literal_eval(atr_dict["grid"])))
            elif atr_dict["layout"] == "place":
                ctrl_.place(**(literal_eval(atr_dict["place"])))
            else:
                print(f"{prefix}, unknown layout of {atr_dict['layout']}")
                return
        else:
            # print(f"{atrDict['text']}: no assemble")
            return

        if "childOpt" in atr_dict:
            for child in ctrl.winfo_children():
                child.grid_configure(**(literal_eval(atr_dict["childOpt"])))

        print(f"{prefix}, layout: {atr_dict['layout']}")

    @override
    def create_xml(self, tag: str, atr_dict: dict[str, str], root: et.Element | None = None) -> et.Element:
        # try:
        if root:
            itm_xml = et.SubElement(root, tag)
        else:
            itm_xml = et.Element(tag)
        itm_xml.attrib = atr_dict.copy()
        return itm_xml
        # except RuntimeError as r:
        #     print(f"\n{tag}:{atr_dict['id']}->errot to create_item: {r}")
 
    @override
    def create_control(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> tuple[str, tk.Misc]:
        tag = ctrl_cfg.tag
        atr_dict = ctrl_cfg.attrib
        text: str = atr_dict.get("text", "")
        id_ctrl: str = ""
        if "id" in atr_dict:
            id_ctrl = atr_dict["id"]
        else:
            id_ctrl = text.replace(" ", "").replace(".", "_").replace("\n", "_")
        print(f"{'  '*level}{tag}, id: {id_ctrl}, text: {text}", end="")

        if id_ctrl in self._ctrls_dict:
            raise ValueError(f"{id_ctrl} already exists")

        options: dict[str, Any] = {}
        if "options" in atr_dict:
            options = eval(atr_dict["options"])

        match tag:
            case "LabelFrame":
                ctrl = ttk.LabelFrame(parent, text=text, **options)
                print()
            case "Frame" | "Tab":
                ctrl = tk.Frame(parent, **options)
                print()
            case "Label":
                ctrl = ttk.Label(parent, text=text, **options)
                clickable = atr_dict.get("clickable", False)
                if clickable:
                    print(f"{id_ctrl} clickable")
                    _= ctrl.bind("<Button-1>",
                        lambda event: self.process_message(id_ctrl, "Clicked"))
            case "Button":
                ctrl = ttk.Button(parent, text=str(text),
                    command=lambda: self.process_message(id_ctrl, "Clicked"),
                    **options)
            case "Canvas":
                ctrl = tk.Canvas(parent, **options)
            case "Checkbutton":
                var_text = atr_dict["var"]
                var_text_name = f"_var{atr_dict['var']}"
                if var_text_name not in self.__dict__:
                    self.__dict__[var_text_name] = tk.IntVar()
                variable: tk.IntVar = self.__dict__[var_text_name]
                ctrl = tk.Checkbutton(parent, text=text,
                    variable=variable, **options)

                # variable.trace("w",
                #     lambda u0, u1, u2: self.process_message(
                #         var_text, "Changed", variable.get()
                #     )
                # )
                # trace_add(self, mode: Literal["array", "read", "write", "unset"], callback: Callable[[str, str, str], object])
                _ = variable.trace_add("write",  lambda u0, u1, u2: self.process_message(
                        var_text, "Changed", variable.get()
                    ))

                if atr_dict["select"] == "1":
                    ctrl.select()
            case "Combobox":
                ctrl = ComboboxCtrl(parent, app=self,
                    id_ctrl=id_ctrl,
                    default=int(atr_dict["default"]),
                    options=options)
            case "Entry":
                ctrl = EntryCtrl(parent, **options)
            case "ImgButton":
                ctrl = ImgBtnCtrl(parent, app=self, text=text,
                    img_file=os.path.join(self._res_path,
                        atr_dict["img"]),
                    command=lambda: self.process_message(id_ctrl,
                        "Clicked"),
                    options=options)
            case "ImgPanel":
                img = atr_dict.get("img", "")
                if img:
                    img = os.path.join(self._res_path, img)
                ctrl = ImgPanel(parent, img, **options)
            case "MatPlot":
                if "size" in atr_dict:
                    size: tuple[float, float] = literal_eval(atr_dict["size"])
                    ctrl = MatPlotCtrl(parent, text, atr_dict["xLabel"],
                        atr_dict["yLabel"], size)
                else:
                    ctrl = MatPlotCtrl(parent, text, atr_dict["xLabel"],
                        atr_dict["yLabel"])
            case "Menu":
                print()
                ctrl = self.create_menu(ctrl_cfg)
            case "Notebook":
                ctrl = ttk.Notebook(parent, **options)
                print()
                for subctrl_cfg in list(ctrl_cfg):
                    _, sub_ctrl = self.create_control(ctrl,
                        subctrl_cfg, level + 1)
                    print(f"tabCtrl: {subctrl_cfg.tag}")
                    ctrl.add(sub_ctrl,
                        text=subctrl_cfg.attrib["text"])
                    for item in list(subctrl_cfg):
                        _ = self.create_controls(sub_ctrl, item,
                            level + 2)
            case "RadiobuttonGroup":
                ctrl = RadiobuttonCtrl(id_ctrl, parent, app=self,
                    text=text, subctrls=list(ctrl_cfg),
                    level=level, options=options)
                print()
            case "Radiobutton":
                var_text = atr_dict["var"]
                var_text_name = f"_var{atr_dict['var']}"
                if var_text_name not in self.__dict__:
                    self.__dict__[var_text_name] = tk.IntVar()
                variable = self.__dict__[var_text_name]
                id_ctrl = var_text
                # print(f", title = {title}", end="")
                ctrl = ttk.Radiobutton(parent, variable=variable,
                    value=int(atr_dict["value"]), text=text,
                    command=lambda: self.process_message(
                        id_ctrl, "Changed", variable.get()))
            case "Statusbar":
                ctrl = MultiStatusBar(parent)
                for subctrl_cfg in list(ctrl_cfg):
                    ctrl.set_label(**subctrl_cfg.attrib)
            case "ScrolledText":
                ctrl = scrolledtext.ScrolledText(parent, **options)
            case "Spinbox":
                ctrl = tk.Spinbox(parent,
                    command=lambda: self.process_message(id_ctrl, "Changed"),
                    **options)
            case "Style":
                ctrl = ttk.Style()
                ctrl.configure(text, **options)
            case "Toolbar":
                ctrl = Toolbar(parent, self, self._res_path,
                    list(ctrl_cfg))
                print()
            case "Scrollbar":
                ctrl = tk.Scrollbar(parent)
                ctrl.configure(**options)
            case "Listbox":
                ctrl = tk.Listbox(parent)
                ctrl.configure(**options)
            case "Dialog":
                ctrl = Dialog(parent, self, text, list(ctrl_cfg), **options)
                print()
            case _:
                raise ValueError(f"{tag}: unknown Control")

        if "tooltip" in atr_dict:
            Hovertip(ctrl, atr_dict["tooltip"], hover_delay=500)

        self._ctrls_dict.setdefault(id_ctrl, ctrl)
        return id_ctrl, ctrl

    def delete_control(self, id_ctrl: str):
        self._ctrls_dict[id_ctrl].destroy()
        del self._ctrls_dict[id_ctrl]

    def disable_control(self, ctrl: tk.Misc, is_disbl: bool = True):
        assert isinstance(ctrl, tk.Widget)
        if is_disbl:
            ctrl.configure(state="disabled")
        else:
            ctrl.configure(state="normal")

    def create_menu(self, menu_root) -> tk.Menu:
        menubar = tk.Menu(self._win)

        def get_cmd(cmd_name, msg, ext_msg=""):
            return lambda: self.process_message(cmd_name, msg, ext_msg)

        def get_cmd_e(cmd_name, msg, ext_msg=""):
            return lambda event: self.process_message(cmd_name, msg, ext_msg)

        for menu_item in list(menu_root):
            atr_dict = menu_item.attrib
            label = atr_dict["Header"]
            print(f"  Menu: {label}")
            menu = tk.Menu(menubar, tearoff=False)

            if "options" in atr_dict:
                options = literal_eval(atr_dict["options"])
            else:
                options = {}

            msg: str = ""
            ext_msg: str = ""
            for sub_menu_itm in list(menu_item):
                tag = sub_menu_itm.tag
                sub_atr_dict = sub_menu_itm.attrib
                if tag == "Separator":
                    menu.add_separator()
                    print(f"    subMenu: {sub_menu_itm.tag}")
                    continue
                if "options" in sub_atr_dict:
                    sub_options = literal_eval(sub_atr_dict["options"])
                else:
                    sub_options = {}
                sub_label = sub_atr_dict["Command"]
                cmd_name = str(sub_label.replace(" ", "").replace("...", ""))
                print(f"    subMenu: {tag} -> {sub_label}")
                if tag == "Checkbutton":
                    var_name = sub_atr_dict["variable"]
                    self.__dict__[f"_{var_name}"] = tk.BooleanVar()
                    var = self.__dict__[f"_{var_name}"]
                    var.set(True)
                    msg = "Changed"
                    ext_msg = var.get()
                    cmd = get_cmd(cmd_name, msg, ext_msg)
                    menu.add_checkbutton(
                        label=sub_label, command=cmd, variable=var, **sub_options
                    )
                elif tag == "MenuItem":
                    msg = "Clicked"
                    ext_msg = ""
                    cmd = get_cmd(cmd_name, msg, ext_msg)
                    menu.add_command(label=sub_label, command=cmd, **sub_options)
                else:
                    print(f"    Unknown Menu: {tag} -> {sub_label}")

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
                    cmd = get_cmd_e(cmd_name, msg, ext_msg)
                    self._win.bind_all(shortcut, cmd)

            menubar.add_cascade(label=label, menu=menu, **options)

        self._win.config(menu=menubar)
        return menubar

    def get_control(self, id_ctrl: str):
        return self._ctrls_dict[id_ctrl]

    def show_info(self, title: str = "", message: str = ""):
        tkMessageBox.showinfo(title, message)

    def show_warn(self, title: str = "", message: str = ""):
        tkMessageBox.showwarning(title, message)

    def show_err(self, title: str = "", message: str = ""):
        tkMessageBox.showerror(title, message)

    def ask_yesno(self, title: str = "", message: str = ""):
        return tkMessageBox.askyesno(title, message)

    def register_eventhandler(self, id_ctrl: str, handler: EventHanlder):
        self._eventhandler_dict[id_ctrl] = handler

    def process_message(self, id_ctrl: str, *args, **kwargs):
        if id_ctrl in ["Exit", "Quit"]:
            self.exit_window()
            return
        if len(self._eventhandler_dict) != 0:
            func = self._eventhandler_dict.get(id_ctrl, None)
            if func is not None:
                return func(*args, **kwargs)
        print(f"undeal msg of {id_ctrl}: {args}, {kwargs}")

    def go(self):
        try:
            before_go = getattr(self, "_before_go")  # get before_go from child
            before_go()
        except AttributeError as r:
            print(f"Warnning to go: {r}")
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
        def process_message(self, id_ctrl, *args, **kwargs):
            match id_ctrl:
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
                case "radSel":
                    values = ["富强民主", "文明和谐", "自由平等","公正法治","爱国敬业","诚信友善"]
                    monty2 = self.get_control("控件示范区2")
                    monty2.configure(text=values[int(args[1])])
                case "chVarUn":
                    check_btn = self.get_control("屈于现实")
                    if int(args[1]) == 1:
                        self.disable_control(check_btn)
                    else:
                        self.disable_control(check_btn, False)
                case "chVarEn":
                    check_btn = self.get_control("遵从内心")
                    if int(args[1]) == 1:
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
                    super().process_message(id_ctrl, *args, **kwargs)


    path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        path = os.path.dirname(os.path.abspath(sys.executable))
    eapp = ExampleApp(path)
    winsample_xml = os.path.join(eapp.path, "resources", "windowSample.xml")
    eapp.create_window(winsample_xml)
    eapp.go()
