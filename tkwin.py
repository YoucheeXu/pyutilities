#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os

# from pathlib import Path
# parentPath = str(Path(sys.path[0]).parent)
# sys.path.insert(0, parentPath)

import tkinter as tk
import tkinter.messagebox as tkMessageBox
import tkinter.filedialog as tkFileDialog
import tkinter.ttk as ttk
# import tkinter.tix as tix
from tkinter import scrolledtext

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

try:
    from logit import pv
    from matplot import MatPlot     # 2.1
except ImportError:
    from pyutilities.logit import pv
    from pyutilities.matplot import MatPlot

# from PIL import Image, ImageTk    # for imgButton
import PIL
import cv2    # for imgPannel

from idlelib.statusbar import MultiStatusBar
from idlelib.tooltip import Hovertip


__version__ = "3.2.0"


class Toolbar(tk.Frame):
    def __init__(self, parent, resPath):
        # super().__init__(self._parent)
        self._parent = parent
        # tk.Frame.__init__(self, parent)
        super().__init__(self._parent)
        self._resPath = resPath
        # self._tooltip = tix.Balloon(root)


class ImgPanel(tk.Label):
    def __init__(self, parent, text="Image Panel"):
        self._parent = parent
        # tk.Label.__init__(self, parent)
        super().__init__(self._parent)
        self.configure(text=text, anchor = tk.CENTER)

    def display_image(self, image):
        # OpenCV represents images in BGR order; however PIL represents
        # images in RGB order, so we need to swap the channels
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # convert the images to PIL format...
        image = PIL.Image.fromarray(image)
        # ...and then to ImageTk format
        image = PIL.ImageTk.PhotoImage(image)

        self.configure(image = image)
        self._image = image


class Control:
    def __init__(self, varTyp="str"):
        if varTyp == "str":
            self._varVal = tk.StringVar()
        elif varTyp == "int":
            self._varVal = tk.IntVar()

    def get_val(self):
        return self._varVal.get()

    def set_val(self, val):
        self._varVal.set(val)


class EntryCtrl(ttk.Entry, Control):
    def __init__(self, parent, **cfgDict):
        super().__init__(parent)
        Control.__init__(self)
        self.configure(textvariable=self._varVal, **cfgDict)


class ComboboxCtrl(ttk.Combobox, Control):
    def __init__(self, parent, **cfgDict):
        super().__init__(parent)
        Control.__init__(self)
        app = cfgDict["app"]

        self.configure(textvariable=self._varVal, **cfgDict["optDict"])
        self.current(cfgDict["default"])
        cmd = lambda event: app.process_message(cfgDict["idCtrl"], "Selected", self._varVal.get())
        self.bind('<<ComboboxSelected>>', cmd)


class RadiobuttonCtrl(ttk.LabelFrame, Control):
    def __init__(self, parent, **cfgDict):
        super().__init__(parent)
        Control.__init__(self, "int")
        self._app = cfgDict["app"]
        self.configure(text=cfgDict["text"], **cfgDict["options"])
        self._radButtons = []

    def add_radiobutton(self, **optDict):
        radbutton = ttk.Radiobutton(master=self, variable=self._varVal, **optDict)
        self._radButtons.append(radbutton)
        return radbutton


# Button, Checkbutton, Entry, Frame, Label, LabelFrame, Menubutton, Radiobutton, Combobox, Separator, Notebook, ScrolledText, Spinbox, PanedWindow, Scale and Scrollbar, Progressbar, Sizegrip and Treeview
'''
TODO:
    * Message Queue             OK
    * ImageButton               OK
    * RatioButtonGroup          OK
    * To options                almost OK
    * FileDialog
    * Enable/Disable            OK
    * Rest Control              PanedWindow, Scale and Scrollbar, Progressbar, Sizegrip and Treeview
    * Accelerator of Menu       OK
    * Accelerator of global     almost OK
    * EntryGroup
    * tooltip                   OK
    * unique of idCtrl
'''
class tkWin(tk.Frame):
    def __init__(self):
        self._frmApp = tk.Tk()
        super().__init__(self._frmApp)

        self._frmApp.protocol("WM_DELETE_WINDOW", self.exit_window)

        self._dictCtrl = {}

    def _center_window(self, width: float, hight: float):
        '''
            设置窗口居中和宽高
            :param Width: 窗口宽度
            :param Hight: 窗口高度
            :return: 无
        '''

        # 获取屏幕宽度和高度
        sw = self._frmApp.winfo_screenwidth()
        sh = self._frmApp.winfo_screenheight()

        # 计算中心坐标
        cen_x = (sw - width) / 2
        cen_y = (sh - hight) / 2 * 0.9

        # 设置窗口大小并居中
        self._frmApp.geometry('%dx%d+%d+%d' %(width, hight, cen_x, cen_y))

    def exit_window(self):
        res = tkMessageBox.askquestion('Exit Application', 'Do you really want to exit?')
        if res == 'yes':
            self._frmApp.destroy()

    def create_window(self, cfgFile: str):
        self._resPath = os.path.dirname(cfgFile)

        elementTree = et.parse(cfgFile)
        win = elementTree.getroot()
        winAttr = win.attrib

        self._title = winAttr["Title"]
        self._frmApp.title(self._title)

        if "Height" in winAttr:
            width = int(winAttr["Width"])
            hight = int(winAttr["Height"])

            self._center_window(width, hight)

        for frm in list(win):
            self._create_controls(self._frmApp, frm, 0)

    def _create_controls(self, parent, cfg, level=0):
        ctrl = self._create_control(parent, cfg, level)
        tag = cfg.tag
        if tag in ["Menu", "Notebook", "RadiobuttonGroup", "Statusbar"]:
            pass
        else:
            for subCfg in list(cfg):
                self._create_controls(ctrl, subCfg, level + 1)
        self._assemble_control(ctrl, cfg.attrib, f"{'  '*level}")

    def _assemble_control(self, ctrl, atrDict, prefix=""):
        # pv(atrDict)
        if "layout" in atrDict:
            if (atrDict["layout"] == "pack"):
                ctrl.pack(**(eval(atrDict["pack"])))
            elif (atrDict["layout"] == "grid"):
                ctrl.grid(**(eval(atrDict["grid"])))
            else:
                print(f"{prefix}, unknown layout of {atrDict['layout']}")
                return
        else:
            # print(f"{atrDict['text']}: no assemble")
            return

        if "childOpt" in atrDict:
            for child in ctrl.winfo_children():
                child.grid_configure(**(eval(atrDict["childOpt"])))

        print(f"{prefix}, layout: {atrDict['layout']}")

    def _create_control(self, parent, control, level=0):
        tag = control.tag
        atrDict = control.attrib

        try:
            text = atrDict["text"]
            # idCtrl = text.replace(" ", "").replace(".", "_").replace("\n", "_").replace(":", "")
            idCtrl = text.replace(" ", "").replace(".", "_").replace("\n", "_")
            print(f"{'  '*level}{tag}, text: {text}", end="")
        except Exception as r:
            print(f"{'  '*level}{tag}->error: {r}", end="")

        if("options" in atrDict):
            optDict = eval(atrDict["options"])
        else:
            optDict = {}

        if tag == "LabelFrame":
            ctrl = ttk.LabelFrame(parent, text=text, **optDict)
            print()
        elif tag == "Frame" or tag == "Tab":
            ctrl = tk.Frame(parent, **optDict)
            print()
        elif tag == "Button":
            cmd = lambda: self.process_message(idCtrl, "Clicked")
            ctrl = ttk.Button(parent, text=str(text), command=cmd, **optDict)
        elif tag == "Canvas":
            ctrl = tk.Canvas(parent, **optDict)
        elif tag == "Checkbutton":
            varText = atrDict['var']
            varTextName = f"_var{atrDict['var']}"
            if varTextName not in self.__dict__:
                self.__dict__[varTextName] = tk.IntVar()
            variable = self.__dict__[varTextName]
            ctrl = tk.Checkbutton(parent, text=text, variable=variable, **optDict)
            cmd = lambda u0, u1, u2: self.process_message(varText, "Changed", variable.get())
            variable.trace('w', cmd)
            if(atrDict["select"] == "1"): ctrl.select()
        elif tag == "Combobox":
            ctrl = ComboboxCtrl(parent, app=self, idCtrl=idCtrl, default=int(atrDict["default"]), optDict=optDict)
        elif tag == "Entry":
            ctrl = EntryCtrl(parent, **optDict)
        elif tag == "ImgButton":
            imgFile = os.path.join(self._resPath, atrDict["img"])
            img = PIL.Image.open(imgFile)
            eimg = PIL.ImageTk.PhotoImage(img)
            cmd = lambda: self.process_message(idCtrl, "Clicked")
            ctrl = tk.Button(parent, image=eimg, relief=tk.FLAT, command=cmd, **optDict)
            ctrl.image = eimg
        elif tag == "ImgPanel":
            ctrl = ImgPanel(parent, text)
        elif tag == "Label":
            ctrl = ttk.Label(parent, text=text, **optDict)
        elif tag == "MatPlot":
            if("size" in atrDict):
                size = eval(atrDict["size"])
                ctrl = MatPlot(parent, text, atrDict["xLabel"], atrDict["yLabel"], size)
            else:
                ctrl = MatPlot(parent, text, atrDict["xLabel"], atrDict["yLabel"])
        elif tag == "Menu":
            print()
            ctrl = self.create_menu(control);
        elif tag == "Notebook":
            ctrl = ttk.Notebook(parent, **optDict)
            print()
            for subCfg in list(control):
                tabCtrl = ttk.Frame(ctrl, **optDict)
                ctrl.add(tabCtrl, text=subCfg.attrib["text"])
                for item in list(subCfg):
                    self._create_controls(tabCtrl, item, level + 1)
        elif tag == "RadiobuttonGroup":
            ctrl = RadiobuttonCtrl(parent, app=self, text=text, options=optDict)
            print()
            for radBtn in list(control):
                radBtnAtrDict = radBtn.attrib
                val = int(radBtnAtrDict["value"])
                cmd = lambda: self.process_message(idCtrl, "Changed", ctrl.get_text())
                text = radBtnAtrDict["text"]
                radbutton = ctrl.add_radiobutton(value=val, text=text, command=cmd)
                print(f"{'  '*(level + 1)}Control: Radiobutton, text: {text}", end="")
                self._assemble_control(radbutton, radBtnAtrDict)
        elif tag == "Radiobutton":
            varText = atrDict['var']
            varTextName = f"_var{atrDict['var']}"
            value = int(atrDict["value"])
            if varTextName not in self.__dict__:
                self.__dict__[varTextName] = tk.IntVar()
            variable = self.__dict__[varTextName]
            idCtrl = varText
            cmd = lambda: self.process_message(idCtrl, "Changed", variable.get())
            # print(f", title = {title}", end="")
            ctrl = ttk.Radiobutton(parent, variable=variable, value=int(atrDict["value"]), text=text, command=cmd)
            # pv(ctrl, end="")
        elif tag == "Statusbar":
            ctrl = MultiStatusBar(parent)
            for label in list(control):
                ctrl.set_label(**label.attrib)
        elif tag == "ScrolledText":
            ctrl = scrolledtext.ScrolledText(parent, **optDict)
        elif tag == "Spinbox":
            cmd = lambda: self.process_message(idCtrl, "Changed")
            ctrl = tk.Spinbox(parent, command=cmd, **optDict)
        elif tag == "Style":
            ctrl = ttk.Style()
            ctrl.configure(text, **optDict)
        elif tag == "Toolbar":
            ctrl = Toolbar(parent, self._resPath)
            # pv(list(control))
            for subCtrl in list(control):
                imgButton = self._create_control(ctrl, subCtrl)
                self._assemble_control(imgButton, subCtrl.attrib)
        else:
            raise Exception(f"{tag}: unknown Control")

        if "tooltip" in atrDict:
            Hovertip(ctrl, atrDict["tooltip"], hover_delay=500)

        self._dictCtrl.setdefault(idCtrl, ctrl)
        # return self._dictCtrl[idCtrl]
        return ctrl

    def disable_control(self, ctrl, disable=True):
        if disable:
            ctrl.configure(state='disabled')
        else:
            ctrl.configure(state='normal')

    def create_menu(self, menuRoot):
        menubar = tk.Menu(self._frmApp)

        def get_cmd(cmdName, msg, extMsg=""):
            return lambda: self.process_message(cmdName, msg, extMsg)

        def get_eCmd(cmdName, msg, extMsg=""):
            return lambda event: self.process_message(cmdName, msg, extMsg)

        for menuItem in list(menuRoot):
            atrDict = menuItem.attrib
            label = atrDict["Header"]
            print(f"  Menu: {label}")
            menu = tk.Menu(menubar, tearoff=False)

            if("options" in atrDict):
                optDict = eval(atrDict["options"])
            else:
                optDict = {}

            for subMenuItm in list(menuItem):
                tag = subMenuItm.tag
                subAtrDict = subMenuItm.attrib
                if tag == "Separator":
                    menu.add_separator()
                    print(f"    subMenu: {subMenuItm.tag}")
                    continue
                if("options" in subAtrDict):
                    subOptDict = eval(subAtrDict["options"])
                else:
                    subOptDict = {}
                subLabel = subAtrDict["Command"]
                cmdName = str(subLabel.replace(" ", "").replace("...", ""))
                print(f"    subMenu: {tag} -> {subLabel}")
                if tag == "Checkbutton":
                    varName = subAtrDict["variable"]
                    self.__dict__[f"_{varName}"] = tk.BooleanVar()
                    var = self.__dict__[f"_{varName}"]
                    var.set(True)
                    msg = "Changed"
                    extMsg = var.get()
                    cmd = get_cmd(cmdName, msg, extMsg)
                    menu.add_checkbutton(label=subLabel, command=cmd, variable=var, **subOptDict)
                elif tag == "MenuItem":
                    msg = "Clicked"
                    extMsg = ""
                    cmd = get_cmd(cmdName, msg, extMsg)
                    menu.add_command(label=subLabel, command=cmd, **subOptDict)
                else:
                    print(f"    Unknown Menu: {tag} -> {subLabel}")

                if "accelerator" in subOptDict:
                    shortcutLst = subOptDict["accelerator"].split("+")
                    shortcut = "<" + shortcutLst[0].replace("Ctrl", "Control").strip() + "-" + shortcutLst[1].lower().strip() + ">"
                    # pv(shortcut)
                    cmd = get_eCmd(cmdName, msg, extMsg)
                    self._frmApp.bind_all(shortcut, cmd)

            menubar.add_cascade(label=label, menu=menu, **optDict)

        self._frmApp.config(menu=menubar)

    def get_control(self, idCtrl):
        return self._dictCtrl[idCtrl]

    def show_info(self, *args):
        if(len(args) == 2):
            tkMessageBox.showinfo(args[0], args[1])
        else:
            tkMessageBox.showinfo(self._title, args[0])

    def show_warn(self, *args):
        if(len(args) == 2):
            tkMessageBox.showwarning(args[0], args[1])
        else:
            tkMessageBox.showwarning(self._title, args[0])

    def show_err(self, *args):
        if(len(args) == 2):
            tkMessageBox.showerror(args[0], args[1])
        else:
            tkMessageBox.showerror(self._title, args[0])

    def ask_yesno(self, *args):
        if(len(args) == 2):
            return tkMessageBox.askyesno(args[0], args[1])
        else:
            return tkMessageBox.askyesno(self._title, args[0])

    def process_message(self, idCtrl, msg, extMsg=""):
        if (idCtrl == "Exit" or idCtrl == "Quit"):
            self.exit_window()
        else:
            print(f"undeal msg of {idCtrl}: {msg}, {extMsg}")

    def go(self):
        self._frmApp.mainloop()

    def get_path(self):
        curPath = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            # print("script is packaged!")
            curPath = os.path.dirname(os.path.abspath(sys.executable))
        return curPath


if __name__ == '__main__':
    class exampleApp(tkWin):
        def __init__(self):
            super().__init__()
        def process_message(self, idCtrl, msg, extMsg=""):
            if idCtrl == "DesignFilter":
                frqLo = float(self.get_control("LowFrequency").get_val())
                pv(frqLo)
            else:
                super().process_message(idCtrl, msg, extMsg)
    eapp = exampleApp()
    curPath = eapp.get_path()
    win_xml = os.path.join(curPath, 'resources', 'windowSample.xml')
    eapp.create_window(win_xml)
    eapp.go()
