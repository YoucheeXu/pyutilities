#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
# sys.dont_write_bytecode = True
import os

import tkinter as tk
import tkinter.messagebox as tkMessageBox
from tkinter import ttk
from tkinter import scrolledtext

import xml.etree.ElementTree as et

try:
    from logit import pv
    from matplot import MatPlot
except ImportError:
    from pyutilities.logit import pv
    from pyutilities.matplot import MatPlot

from idlelib.statusbar import MultiStatusBar
from idlelib.tooltip import Hovertip

# from PIL import Image, ImageTk    # for imgButton
import PIL
# import cv2    # for imgPannel


__version__ = "3.2.2"


class Toolbar(tk.Frame):
    def __init__(self, parent, res_path):
        # super().__init__(self._parent)
        self._parent = parent
        # tk.Frame.__init__(self, parent)
        super().__init__(self._parent)
        self._res_path = res_path
        # self._tooltip = tix.Balloon(root)


class ImgPanel(tk.Label):
    def __init__(self, parent, img_file: str, **opt_dict):
        self._parent = parent
        # tk.Label.__init__(self, parent)
        super().__init__(self._parent)
        img = self.read_image(img_file,opt_dict["width"], opt_dict["height"])
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
        # if "textvariable" in optDict:
            # varText = optDict['textvariable']
            # varTextName = varText[varText.rfind('.') + 1:]
            # print(f'\nvarTextName: {varTextName}')
            # if varTextName not in self.__dict__:
                # self.__dict__[varTextName] = tk.StringVar()
            # # variable = self.__dict__[varTextName]
        self.configure(textvariable=self._var_val, **cfg_dict)


class ComboboxCtrl(ttk.Combobox, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        Control.__init__(self)
        app = cfg_dict["app"]

        self.configure(textvariable=self._var_val, **cfg_dict["optDict"])
        self.current(cfg_dict["default"])
        # cmd = lambda event: app.process_message(cfgDict["idCtrl"], "Selected", self._varVal.get())
        def cmd(event):
            app.process_message(cfg_dict["idCtrl"], "Selected", self._var_val.get())
        self.bind('<<ComboboxSelected>>', cmd)


class RadiobuttonCtrl(ttk.LabelFrame, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        Control.__init__(self, "int")
        self._app = cfg_dict["app"]
        self.configure(text=cfg_dict["text"], **cfg_dict["options"])
        self._radbuttons_lst = []

    def add_radiobutton(self, **optDict):
        radbutton = ttk.Radiobutton(master=self, variable=self._var_val, **optDict)
        self._radbuttons_lst.append(radbutton)
        return radbutton


class ImgBtnCtrl(tk.Button, Control):
    def __init__(self, parent, **cfg_dict):
        super().__init__(parent)
        # Control.__init__(self, "int")
        self._app = cfg_dict["app"]
        img_file = cfg_dict["imgFile"]
        # print(f"\ncfgDict: {cfgDict}")
        opt_dict = cfg_dict["options"]
        cmd = cfg_dict["command"]
        eimg = self.read_image(img_file, opt_dict["width"], opt_dict["height"])
        # cmd = lambda: self._app.process_message(idCtrl, "Clicked")
        if "text" in cfg_dict:
            self.configure(image=eimg, command=cmd, compound=tk.LEFT, relief=tk.FLAT, **opt_dict)
        else:
            self.configure(image=eimg, command=cmd, relief=tk.FLAT, **opt_dict)
        self.image = eimg

    def read_image(self, img_file: str, w: int, h: int):
        img = PIL.Image.open(img_file)
        img = img.resize((w, h))
        eimg = PIL.ImageTk.PhotoImage(img)
        return eimg

    def read_image2(self, img_file: str, w: int, h: int):
        # Creating a photoimage object to use image
        photo = tk.PhotoImage(file=img_file)

        # Resizing image to fit on button
        photoimage = photo.subsample(w, h)

        return photoimage


class tkWin(tk.Frame):
    def __init__(self):
        self._frm_app = tk.Tk()
        super().__init__(self._frm_app)

        self._frm_app.protocol("WM_DELETE_WINDOW", self.exit_window)

        self._ctrls_dict = {}

        self._cur_path = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            # print("script is packaged!")
            self._cur_path = os.path.dirname(os.path.abspath(sys.executable))

    def _center_window(self, width: int, hight: int):
        ''' 设置窗口居中和宽高

        Args:
            width (int): 窗口宽度
            hight (int): 窗口高度

        Returns:
            None
        '''

        # 获取屏幕宽度和高度
        sw = self._frm_app.winfo_screenwidth()
        sh = self._frm_app.winfo_screenheight()

        # 计算中心坐标
        cen_x = (sw - width) / 2
        cen_y = (sh - hight) / 2 * 0.9

        # 设置窗口大小并居中
        # self._frmApp.geometry('%dx%d+%d+%d' %(width, hight, cen_x, cen_y))
        self._frm_app.geometry(f"{int(width)}x{int(hight)}+{int(cen_x)}+{int(cen_y)}")

    def exit_window(self):
        res = tkMessageBox.askquestion('Exit Application', 'Do you really want to exit?')
        if res == 'yes':
            try:
                before_close = getattr(self, '_before_close')    # get before_close from child
                before_close()
            except Exception as r:
                print(f"error to exit: {r}")
            self._frm_app.destroy()

    def create_window(self, cfgFile: str):
        self._res_path = os.path.dirname(cfgFile)

        element_tree = et.parse(cfgFile)
        win = element_tree.getroot()
        win_attr = win.attrib

        self._title = win_attr["Title"]
        self._frm_app.title(self._title)

        if "Height" in win_attr:
            width = int(win_attr["Width"])
            hight = int(win_attr["Height"])

            self._center_window(width, hight)

        for frm in list(win):
            self._create_controls(self._frm_app, frm, 0)

    def _create_controls(self, parent, cfg, level=0):
        ctrl = self.create_control(parent, cfg, level)
        tag = cfg.tag
        if tag in ["Menu", "Notebook", "RadiobuttonGroup", "Statusbar"]:
            pass
        else:
            for sub_cfg in list(cfg):
                self._create_controls(ctrl, sub_cfg, level + 1)
        self.assemble_control(ctrl, cfg.attrib, f"{'  '*level}")

    def assemble_control(self, ctrl, atr_dict, prefix=""):
        if "layout" in atr_dict:
            if atr_dict["layout"] == "pack":
                ctrl.pack(**(eval(atr_dict["pack"])))
            elif atr_dict["layout"] == "grid":
                ctrl.grid(**(eval(atr_dict["grid"])))
            elif atr_dict["layout"] == "place":
                ctrl.place(**(eval(atr_dict["place"])))
            else:
                print(f"{prefix}, unknown layout of {atr_dict['layout']}")
                return
        else:
            # print(f"{atrDict['text']}: no assemble")
            return

        if "childOpt" in atr_dict:
            for child in ctrl.winfo_children():
                child.grid_configure(**(eval(atr_dict["childOpt"])))

        print(f"{prefix}, layout: {atr_dict['layout']}")

    def create_control(self, parent, control, level=0):
        tag = control.tag
        atr_dict = control.attrib
        id_ctrl = ""

        try:
            text = ""
            if "id" in atr_dict:
                id_ctrl = atr_dict["id"]
            else:
                text = atr_dict["text"]
                # idCtrl = text.replace(" ", "").replace(".", "_").replace("\n", "_").replace(":", "")
                id_ctrl = text.replace(" ", "").replace(".", "_").replace("\n", "_")
            print(f"{'  '*level}{tag}, id: {id_ctrl}, text: {text}", end="")
        except Exception as r:
            print(f"{'  '*level}{tag}: {id_ctrl}->error1: {r}", end="")

        if id_ctrl in self._ctrls_dict:
            raise ValueError(f"{id_ctrl} already exists")

        if "options" in atr_dict:
            optDict = eval(atr_dict["options"])
        else:
            optDict = {}

        try:
            match tag:
                case "LabelFrame":
                    ctrl = ttk.LabelFrame(parent, text=text, **optDict)
                    print()
                case "Frame" | "Tab":
                    ctrl = tk.Frame(parent, **optDict)
                    print()
                case "Button":
                    # cmd = lambda: self.process_message(idCtrl, "Clicked")
                    def cmd():
                        self.process_message(id_ctrl, "Clicked")
                    ctrl = ttk.Button(parent, text=str(text), command=cmd, **optDict)
                case "Canvas":
                    ctrl = tk.Canvas(parent, **optDict)
                case "Checkbutton":
                    var_text = atr_dict['var']
                    var_text_name = f"_var{atr_dict['var']}"
                    if var_text_name not in self.__dict__:
                        self.__dict__[var_text_name] = tk.IntVar()
                    variable = self.__dict__[var_text_name]
                    ctrl = tk.Checkbutton(parent, text=text, variable=variable, **optDict)
                    # cmd = lambda u0, u1, u2: self.process_message(varText, "Changed", variable.get())
                    def cmd():
                        self.process_message(var_text, "Changed", variable.get())
                    variable.trace('w', cmd)
                    if atr_dict["select"] == "1":
                        ctrl.select()
                case "Combobox":
                    ctrl = ComboboxCtrl(parent, app=self, idCtrl=id_ctrl, default=int(atr_dict["default"]), optDict=optDict)
                case "Entry":
                    ctrl = EntryCtrl(parent, **optDict)
                case "ImgButton":
                    # imgFile = os.path.join(self._resPath, atrDict["img"])
                    # img = PIL.Image.open(imgFile)
                    # img = img.resize((optDict["width"], optDict["height"]))
                    # eimg = PIL.ImageTk.PhotoImage(img)
                    # # photo = tk.PhotoImage(file=imgFile)
                    # # Resizing image to fit on button
                    # # eimg = photo.subsample(optDict["width"], optDict["height"])
                    # cmd = lambda: self.process_message(idCtrl, "Clicked")
                    # ctrl = tk.Button(parent, image=eimg, relief=tk.FLAT, command=cmd, **optDict)
                    # ctrl.image = eimg
                    img_file = os.path.join(self._res_path, atr_dict["img"])
                    # cmd = lambda: self.process_message(idCtrl, "Clicked")
                    def cmd():
                        self.process_message(id_ctrl, "Clicked")
                    ctrl = ImgBtnCtrl(parent, app=self, imgFile=img_file, command=cmd, options=optDict)
                case "ImgPanel":
                    img_file = os.path.join(self._res_path, atr_dict["img"])
                    ctrl = ImgPanel(parent, img_file, **optDict)
                case "Label":
                    ctrl = ttk.Label(parent, text=text, **optDict)
                case "MatPlot":
                    if "size" in atr_dict:
                        size = eval(atr_dict["size"])
                        ctrl = MatPlot(parent, text, atr_dict["xLabel"], atr_dict["yLabel"], size)
                    else:
                        ctrl = MatPlot(parent, text, atr_dict["xLabel"], atr_dict["yLabel"])
                case "Menu":
                    print()
                    ctrl = self.create_menu(control)
                case "Notebook":
                    ctrl = ttk.Notebook(parent, **optDict)
                    print()
                    for sub_cfg in list(control):
                        # tabCtrl = ttk.Frame(ctrl, **optDict)
                        tab_ctrl = self.create_control(ctrl, sub_cfg, level + 1)
                        print(f"tabCtrl: {sub_cfg.tag}")
                        ctrl.add(tab_ctrl, text=sub_cfg.attrib["text"])
                        for item in list(sub_cfg):
                            self._create_controls(tab_ctrl, item, level + 2)
                case "RadiobuttonGroup":
                    ctrl = RadiobuttonCtrl(parent, app=self, text=text, options=optDict)
                    print()
                    for radbtn in list(control):
                        radbtn_atr_dict = radbtn.attrib
                        val = int(radbtn_atr_dict["value"])
                        # cmd = lambda: self.process_message(idCtrl, "Changed", ctrl.get_text())
                        def cmd():
                            self.process_message(id_ctrl, "Changed", ctrl.get_val())
                        text = radbtn_atr_dict["text"]
                        radbutton = ctrl.add_radiobutton(value=val, text=text, command=cmd)
                        print(f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
                        self.assemble_control(radbutton, radbtn_atr_dict)
                case "Radiobutton":
                    var_text = atr_dict['var']
                    var_text_name = f"_var{atr_dict['var']}"
                    # value = int(atrDict["value"])
                    if var_text_name not in self.__dict__:
                        self.__dict__[var_text_name] = tk.IntVar()
                    variable = self.__dict__[var_text_name]
                    id_ctrl = var_text
                    # cmd = lambda: self.process_message(idCtrl, "Changed", variable.get())
                    def cmd():
                        self.process_message(id_ctrl, "Changed", variable.get())
                    # print(f", title = {title}", end="")
                    ctrl = ttk.Radiobutton(parent, variable=variable, value=int(atr_dict["value"]), text=text, command=cmd)
                    # pv(ctrl, end="")
                case "Statusbar":
                    ctrl = MultiStatusBar(parent)
                    for label in list(control):
                        ctrl.set_label(**label.attrib)
                case "ScrolledText":
                    ctrl = scrolledtext.ScrolledText(parent, **optDict)
                case "Spinbox":
                    # cmd = lambda: self.process_message(idCtrl, "Changed")
                    def cmd():
                        self.process_message(id_ctrl, "Changed")
                    ctrl = tk.Spinbox(parent, command=cmd, **optDict)
                case "Style":
                    ctrl = ttk.Style()
                    ctrl.configure(text, **optDict)
                case "Toolbar":
                    ctrl = Toolbar(parent, self._res_path)
                    # pv(list(control))
                    for sub_ctrl in list(control):
                        imgbutton = self.create_control(ctrl, sub_ctrl)
                        self.assemble_control(imgbutton, sub_ctrl.attrib)
                case "Scrollbar":
                    # cmd = lambda: self.process_message(idCtrl, "Changed")
                    ctrl = tk.Scrollbar(parent)
                    ctrl.configure(**optDict)
                case "Listbox":
                    ctrl = tk.Listbox(parent)
                    ctrl.configure(**optDict)
                case _:
                    raise ValueError(f"{tag}: unknown Control")
        except Exception as r:
            print(f"\n{'  '*level}{tag}: {id_ctrl}->error2: {r}", end="")

        if "tooltip" in atr_dict:
            Hovertip(ctrl, atr_dict["tooltip"], hover_delay=500)

        self._ctrls_dict.setdefault(id_ctrl, ctrl)
        # return self._dictCtrl[idCtrl]
        return ctrl

    def disable_control(self, ctrl, is_disbl=True):
        if is_disbl:
            ctrl.configure(state='disabled')
        else:
            ctrl.configure(state='normal')

    def create_menu(self, menu_root):
        menubar = tk.Menu(self._frm_app)

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
                opt_dict = eval(atr_dict["options"])
            else:
                opt_dict = {}

            for sub_menu_itm in list(menu_item):
                tag = sub_menu_itm.tag
                sub_atr_dict = sub_menu_itm.attrib
                if tag == "Separator":
                    menu.add_separator()
                    print(f"    subMenu: {sub_menu_itm.tag}")
                    continue
                if "options" in sub_atr_dict:
                    sub_opt_dict = eval(sub_atr_dict["options"])
                else:
                    sub_opt_dict = {}
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
                    menu.add_checkbutton(label=sub_label, command=cmd, variable=var, **sub_opt_dict)
                elif tag == "MenuItem":
                    msg = "Clicked"
                    ext_msg = ""
                    cmd = get_cmd(cmd_name, msg, ext_msg)
                    menu.add_command(label=sub_label, command=cmd, **sub_opt_dict)
                else:
                    print(f"    Unknown Menu: {tag} -> {sub_label}")

                if "accelerator" in sub_opt_dict:
                    shortcut_lst = sub_opt_dict["accelerator"].split("+")
                    shortcut = "<" + shortcut_lst[0].replace("Ctrl", "Control").strip() + "-" + shortcut_lst[1].lower().strip() + ">"
                    # pv(shortcut)
                    cmd = get_cmd_e(cmd_name, msg, ext_msg)
                    self._frm_app.bind_all(shortcut, cmd)

            menubar.add_cascade(label=label, menu=menu, **opt_dict)

        self._frm_app.config(menu=menubar)
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

    def process_message(self, id_ctrl, msg, ext_msg=""):
        if id_ctrl in ["Exit", "Quit"]:
            self.exit_window()
        else:
            print(f"undeal msg of {id_ctrl}: {msg}, {ext_msg}")

    def go(self):
        try:
            before_go = getattr(self, '_before_go')    # get before_go from child
            before_go()
        except Exception as r:
            print(f"error to go: {r}")
        self._frm_app.mainloop()

    def get_path(self):
        return self._cur_path


if __name__ == '__main__':
    class ExampleApp(tkWin):
        def __init__(self):
            super().__init__()
        def process_message(self, id_ctrl, msg, ext_msg=""):
            if id_ctrl == "DesignFilter":
                frq_low = float(self.get_control("LowFrequency").get_val())
                pv(frq_low)
            else:
                super().process_message(id_ctrl, msg, ext_msg)
    app = ExampleApp()
    cur_path = app.get_path()
    # winSampleXml = os.path.join(curPath, 'resources', 'window3_2Sample1.xml')
    winSampleXml = os.path.join(cur_path, 'resources', 'windowSample.xml')
    app.create_window(winSampleXml)
    app.go()
