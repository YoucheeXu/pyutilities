#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
import platform
import ctypes
from collections.abc import Callable

import tkinter as tk
import tkinter.messagebox as tkMessageBox
from tkinter import ttk
from tkinter import scrolledtext
import xml.etree.ElementTree as et
from ast import literal_eval

try:
    from logit import pv, pe
    from matplot import MatPlot
except ImportError:
    from pyutilities.logit import pv, pe
    from pyutilities.matplot import MatPlot

from idlelib.statusbar import MultiStatusBar
from idlelib.tooltip import Hovertip

# from PIL import Image, ImageTk    # for imgButton
import PIL

EventHanlder = Callable[[str, str], None]
DlgCallback = Callable[[bool], (bool, str)]

__version__ = "3.3.0"
IS_WINDOWS = platform.system() == "Windows"


class Toolbar(tk.Frame):
    def __init__(self, parent, res_path):
        # super().__init__(self._parent)
        self._parent = parent
        # tk.Frame.__init__(self, parent)
        super().__init__(self._parent)
        self._res_path = res_path
        # self._tooltip = tix.Balloon(root)


class ImgPanel(tk.Label):
    def __init__(self, parent, img_file: str, **options):
        self._parent = parent
        # tk.Label.__init__(self, parent)
        super().__init__(self._parent)
        img = self.read_image(img_file, options["width"], options["height"])
        self.configure(text="", image=img, anchor=tk.CENTER)
        self.image = img

    # def read_image(self, imgFile):
    # # Creating a photoimage object to use image
    # photo = tk.PhotoImage(file=imgFile)

    # # # Resizing image to fit on button
    # # photoimage = photo.subsample(3, 3)

    # return photo

    def read_image(self, img_file: str, w: int, h: int):
        img = PIL.Image.open(img_file)
        img = img.resize((w, h))
        eimg = PIL.ImageTk.PhotoImage(img)
        return eimg

    # def display_image(self, img):
    # # OpenCV represents images in BGR order however PIL represents
    # # images in RGB order, so we need to swap the channels
    # image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # # convert the images to PIL format...
    # image = PIL.Image.fromarray(image)
    # # ...and then to ImageTk format
    # image = PIL.ImageTk.PhotoImage(image)

    # self.configure(image = image)
    # self._image = image


class Dialog(ttk.Frame):
    def __init__(self, parent, title: str, subctrl_list, options) -> None:
        super().__init__(self, parent.win, **options)
        self._top = None
        self._parent = parent
        self._title = title
        self._subctrl_list = subctrl_list
        # self._options = options
        self._confirm = False
        self._confirm_handler: DlgCallback = None
        self._id_list = []

    def do_show(self):
        # self.deiconify()
        win = self._parent.win
        self._top = tk.Toplevel(win)
        self._top.title(self._title)
        # place dialog below parent if running htest
        self._top.geometry("+%d+%d" % (
                        win.winfo_rootx()+30,
                        win.winfo_rooty()+30))
        self._top.resizable(0, 0)
        self._top.protocol("WM_DELETE_WINDOW", self.destroy) # intercept close button

        # self.resizable(0, 0)        # 禁止调节大小
        # self.withdraw()
        parent = self._parent
        id_ctrl = self._title.replace(" ", "").replace(".", "_").replace("\n", "_")

        frm_dlg_xml = parent.create_xml("Top", {})

        frm_main_xml = parent.create_xml("Frame", {"text": f"frmMain{id_ctrl}"}, frm_dlg_xml)
        id_frmain, frm_main = parent.create_control(self._top, frm_main_xml, 0)
        self._id_list.append(id_frmain)

        for sub_ctrl in self._subctrl_list:
            id_, ctrl = parent.create_control(frm_main, sub_ctrl, 1)
            self._id_list.append(id_)
            parent.assemble_control(ctrl, sub_ctrl.attrib, f"{'  '*1}")

        parent.assemble_control(frm_main, {"layout": "pack",
            "pack": "{'side':'top','fill':'both','expand':True,'padx':5,'pady':5}"})

        frm_bot_xml = parent.create_xml("Frame", {"text": f"frmBot{id_ctrl}"}, frm_dlg_xml)
        id_frmbot, frm_bot = parent.create_control(self._top, frm_bot_xml, 0)
        self._id_list.append(id_frmbot)

        xml = parent.create_xml("Button", {"id": f"btnConfirm{id_ctrl}",
            "text": "Confirm", "options": "{'width':20}"}, frm_bot_xml)
        id_, ctrl = parent.create_control(frm_bot, xml, 1)
        self._id_list.append(id_)
        parent.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")
        parent.register_eventhandler(id_, self._do_confirm)

        xml = parent.create_xml("Button", {"id": f"btnCancel{id_ctrl}",
            "text": "Cancel", "options": "{'width':20}"}, frm_bot_xml)
        id_, ctrl = parent.create_control(frm_bot, xml, 1)
        self._id_list.append(id_)
        parent.assemble_control(ctrl, {"layout":"pack",
            "pack":"{'side':'right','fill':'both','expand':True,'padx':5,'pady':5}"}, f"{'  '*1}")
        parent.register_eventhandler(id_, self._do_cancel)

        parent.assemble_control(frm_bot, {"layout": "pack",
            "pack": "{'side':'bottom','fill':'both','expand':True,'padx':5,'pady':5}"})

        # self._top.wait_visibility() # can't grab until window appears, so we wait
        self._top.transient(win)   # dialog window is related to main
        self._top.grab_set()        # ensure all input goes to our window
        # 设置achieved_value，使该窗口始终处于其他窗口的上层
        self._top.attributes("-topmost", 1)
        self.wait_window(self._top)

    def get_control(self, id_: str):
        return self._parent.get_control(id_)

    def _do_cancel(self, msg, ext_msg=""):
        self._confirm = False
        print(msg, ext_msg)
        self.destroy()

    def _do_confirm(self, msg, ext_msg=""):
        self._confirm = True
        print(msg, ext_msg)
        self.destroy()

    def register_confirmhandler(self, handler: DlgCallback):
        self._confirm_handler = handler

    def destroy(self):
        # self.withdraw()
        if self._top:
            if self._confirm_handler:
                ret, msg = self._confirm_handler(self._confirm)
                if not ret:
                    self._parent.show_err(self._title, msg)
                    return
            self._top.grab_release()
            for id_ctrl in self._id_list:
                self._parent.delete_control(id_ctrl)
            self._id_list.clear()
            self._top.destroy()
            self._top = None


class Control:
    def __init__(self, var_typ="str"):
        if var_typ == "str":
            self._var_val = tk.StringVar()
        elif var_typ == "int":
            self._var_val = tk.IntVar()

    def get_val(self):
        return self._var_val.get()

    def set_val(self, val):
        self._var_val.set(val)


class EntryCtrl(ttk.Entry, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        Control.__init__(self)
        self.configure(textvariable=self._var_val, **cfg_dict)


class ComboboxCtrl(ttk.Combobox, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        Control.__init__(self)
        app = cfg_dict["app"]
        self.configure(textvariable=self._var_val, **cfg_dict["options"])
        self.current(cfg_dict["default"])
        self.bind(
            "<<ComboboxSelected>>",
            lambda event: app.process_message(
                cfg_dict["id_ctrl"], "Selected", self._var_val.get()
            ),
        )


class RadiobuttonCtrl(ttk.LabelFrame, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        Control.__init__(self, "int")
        self._app = cfg_dict["app"]
        self.configure(text=cfg_dict["text"], **cfg_dict["options"])
        self._radbuttons_lst = []

    def add_radiobutton(self, **opt_dict):
        radbutton = ttk.Radiobutton(master=self, variable=self._var_val, **opt_dict)
        self._radbuttons_lst.append(radbutton)
        return radbutton


class ImgBtnCtrl(tk.Button, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        # Control.__init__(self, "int")
        self._app = cfg_dict["app"]
        img_file = cfg_dict["img_file"]
        # print(f"\ncfgDict: {cfgDict}")
        options = cfg_dict["options"]
        # self._options = cfg_dict["options"].copy()
        # self._w = options.copy()["width"]
        # self._h = options.copy()["height"]
        # pv(type(options))
        cmd = cfg_dict["command"]
        eimg = self._read_image(img_file)
        if "text" in cfg_dict:
            self.configure(
                image=eimg, command=cmd, compound=tk.LEFT, relief=tk.FLAT, **options
            )
        else:
            self.configure(image=eimg, command=cmd, relief=tk.FLAT, **options)
        self.image = eimg

    def _read_image(self, img_file: str):
        # eimg = PIL.ImageTk.PhotoImage(img)
        img = PIL.Image.open(img_file)
        # w = self._options["width"]
        # h = self._options["height"]
        # img = img.resize((w, h))
        eimg = PIL.ImageTk.PhotoImage(img)
        return eimg

    def _read_image2(self, img_file: str, w: int, h: int):
        # Creating a photoimage object to use image
        photo = tk.PhotoImage(file=img_file)

        # Resizing image to fit on button
        photoimage = photo.subsample(w, h)

        return photoimage

    # TODO: wait to test
    def change_image(self, img_file: str) -> str:
        eimg = self._read_image(img_file)
        self.configure(image=eimg)


class tkWin:
    def __init__(self, cur_path: str):
        self._win = tk.Tk()

        if IS_WINDOWS:
            try:  # >= win 8.1
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:  # win 8.0 or less
                ctypes.windll.user32.SetProcessDPIAware()
            # ctypes.windll.shcore.SetProcessDpiAwareness(1)
            scale_fact = ctypes.windll.shcore.GetScaleFactorForDevice(0)
            self._win.tk.call("tk", "scaling", scale_fact / 90)

        self._win.protocol("WM_DELETE_WINDOW", self.exit_window)
        # self._win.columnconfigure(0, weight=1)
        # self._win.rowconfigure(0, weight=1)

        self._ctrls_dict = {}
        self._event_hanlder = {}
        self._cur_path = cur_path

        self._title = ""
        self._res_path = ""

    @property
    def win(self):
        return self._win

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
        cen_y = (sh - hight) / 2 * 0.9

        # 设置窗口大小并居中
        self._win.geometry(f"{int(width)}x{int(hight)}+{int(cen_x)}+{int(cen_y)}")

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
            self._create_controls(self._win, frm)

    def _create_controls(self, parent, cfg, level=0):
        _, ctrl = self.create_control(parent, cfg, level)
        tag = cfg.tag
        if tag in ["Menu", "Notebook", "RadiobuttonGroup", "Statusbar", "Dialog"]:
            pass
        else:
            for sub_cfg in list(cfg):
                self._create_controls(ctrl, sub_cfg, level + 1)
        self.assemble_control(ctrl, cfg.attrib, f"{'  '*level}")

    def assemble_control(self, ctrl, atr_dict, prefix=""):
        if "layout" in atr_dict:
            if atr_dict["layout"] == "pack":
                ctrl.pack(**(literal_eval(atr_dict["pack"])))
            elif atr_dict["layout"] == "grid":
                ctrl.grid(**(literal_eval(atr_dict["grid"])))
            elif atr_dict["layout"] == "place":
                ctrl.place(**(literal_eval(atr_dict["place"])))
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

    def create_xml(self, tag: str, atr_dict, root=None):
        try:
            if root:
                itm_xml = et.SubElement(root, tag)
            else:
                itm_xml = et.Element(tag)
            itm_xml.attrib = atr_dict.copy()
        except RuntimeError as r:
            print(f"\n{tag}:{atr_dict['id']}->errot to create_item: {r}")
        return itm_xml

    def create_control(self, parent, control, level=0):
        tag = control.tag
        atr_dict = control.attrib
        text = atr_dict.get("text", None)
        if "id" in atr_dict:
            id_ctrl = atr_dict["id"]
        else:
            id_ctrl = text.replace(" ", "").replace(".", "_").replace("\n", "_")
        print(f"{'  '*level}{tag}, id: {id_ctrl}, text: {text}", end="")

        if id_ctrl in self._ctrls_dict:
            raise ValueError(f"{id_ctrl} already exists")

        if "options" in atr_dict:
            options = eval(atr_dict["options"])
        else:
            options = {}

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
                    ctrl.bind("<Button-1>", lambda event: self.process_message(id_ctrl, "Clicked"))
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
                variable = self.__dict__[var_text_name]
                ctrl = tk.Checkbutton(parent, text=text, variable=variable, **options)
                variable.trace("w",
                    lambda u0, u1, u2: self.process_message(
                        var_text, "Changed", variable.get()
                    )
                )
                if atr_dict["select"] == "1":
                    ctrl.select()
            case "Combobox":
                ctrl = ComboboxCtrl(parent, app=self, id_ctrl=id_ctrl,
                    default=int(atr_dict["default"]), options=options)
            case "Entry":
                ctrl = EntryCtrl(parent, **options)
            case "ImgButton":
                ctrl = ImgBtnCtrl(parent, app=self,
                    img_file=os.path.join(self._res_path,
                        atr_dict["img"]),
                    command=lambda: self.process_message(id_ctrl,
                        "Clicked"),
                    options=options)
            case "ImgPanel":
                ctrl = ImgPanel(parent,
                    os.path.join(self._res_path, atr_dict["img"]), **options)
            case "MatPlot":
                if "size" in atr_dict:
                    size = literal_eval(atr_dict["size"])
                    ctrl = MatPlot(parent, text, atr_dict["xLabel"],
                        atr_dict["yLabel"], size)
                else:
                    ctrl = MatPlot(parent, text, atr_dict["xLabel"],
                        atr_dict["yLabel"])
            case "Menu":
                print()
                ctrl = self.create_menu(control)
            case "Notebook":
                ctrl = ttk.Notebook(parent, **options)
                print()
                for subctrl_cfg in list(control):
                    _, sub_ctrl = self.create_control(ctrl, subctrl_cfg, level + 1)
                    print(f"tabCtrl: {subctrl_cfg.tag}")
                    ctrl.add(sub_ctrl, text=subctrl_cfg.attrib["text"])
                    for item in list(subctrl_cfg):
                        self._create_controls(sub_ctrl, item, level + 2)
            case "RadiobuttonGroup":
                ctrl = RadiobuttonCtrl(parent, app=self,
                    text=text, options=options)
                print()
                for subctrl_cfg in list(control):
                    radbtn_atr_dict = subctrl_cfg.attrib
                    val = int(radbtn_atr_dict["value"])
                    text = radbtn_atr_dict["text"]
                    sub_ctrl = ctrl.add_radiobutton(value=val, text=text,
                        command=lambda: self.process_message(
                            id_ctrl, "Changed", ctrl.get_text()))
                    print(
                        f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
                    self.assemble_control(sub_ctrl, radbtn_atr_dict)
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
                for subctrl_cfg in list(control):
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
                ctrl = Toolbar(parent, self._res_path)
                for subctrl_cfg in list(control):
                    _, sub_ctrl = self.create_control(ctrl, subctrl_cfg)
                    self.assemble_control(sub_ctrl, subctrl_cfg.attrib)
            case "Scrollbar":
                ctrl = tk.Scrollbar(parent)
                ctrl.configure(**options)
            case "Listbox":
                ctrl = tk.Listbox(parent)
                ctrl.configure(**options)
            case "Dialog":
                subctrl_cfg = list(control)
                ctrl = Dialog(self, text, subctrl_cfg, options)
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

    def disable_control(self, ctrl, is_disbl=True):
        if is_disbl:
            ctrl.configure(state="disabled")
        else:
            ctrl.configure(state="normal")

    def create_menu(self, menu_root):
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
        # return menubar

    def get_control(self, id_ctrl: str):
        return self._ctrls_dict[id_ctrl]

    def show_info(self, *args):
        if len(args) == 2:
            tkMessageBox.showinfo(args[0], args[1])
        else:
            tkMessageBox.showinfo(self._title, args[0])

    def show_warn(self, *args):
        if len(args) == 2:
            tkMessageBox.showwarning(args[0], args[1])
        else:
            tkMessageBox.showwarning(self._title, args[0])

    def show_err(self, *args):
        if len(args) == 2:
            tkMessageBox.showerror(args[0], args[1])
        else:
            tkMessageBox.showerror(self._title, args[0])

    def ask_yesno(self, *args):
        if len(args) == 2:
            return tkMessageBox.askyesno(args[0], args[1])
        return tkMessageBox.askyesno(self._title, args[0])

    def register_eventhandler(self, id_ctrl: str, handler: EventHanlder):
        # print(f"register: {id_ctrl}")
        self._event_hanlder[id_ctrl] = handler

    def process_message(self, id_ctrl:str, msg, ext_msg=""):
        if id_ctrl in ["Exit", "Quit"]:
            self.exit_window()
        if len(self._event_hanlder) != 0:
            func = self._event_hanlder.get(id_ctrl, None)
            if func is not None:
                func(msg, ext_msg)
                return
        print(f"undeal msg of {id_ctrl}: {msg}, {ext_msg}")

    def go(self):
        try:
            before_go = getattr(self, "_before_go")  # get before_go from child
            before_go()
        except AttributeError as r:
            print(f"Warnning to go: {r}")
        self._win.mainloop()

    @property
    def path(self):
        return self._cur_path


if __name__ == "__main__":
    class ExampleApp(tkWin):
        def process_message(self, id_ctrl, msg, ext_msg=""):
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
                    monty2.configure(text=values[int(ext_msg)])
                case "chVarUn":
                    check_btn = self.get_control("屈于现实")
                    if int(ext_msg) == 1:
                        self.disable_control(check_btn)
                    else:
                        self.disable_control(check_btn, False)
                case "chVarEn":
                    check_btn = self.get_control("遵从内心")
                    if int(ext_msg) == 1:
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
                    super().process_message(id_ctrl, msg, ext_msg)


    path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        path = os.path.dirname(os.path.abspath(sys.executable))
    eapp = ExampleApp(path)
    winsample_xml = os.path.join(eapp.path, "resources", "windowSample.xml")
    eapp.create_window(winsample_xml)
    eapp.go()
