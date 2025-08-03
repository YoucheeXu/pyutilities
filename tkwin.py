#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from matplot import AxisData
import sys
import os
from typing import Any, cast

import tkinter as tk
import tkinter.messagebox as tkMessageBox
import tkinter.ttk as ttk

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

try:
    from logit import pv, po
    from matplot import AxisData, MatPlot
except ImportError:
    from pyutilities.logit import pv
    from pyutilities.matplot import AxisData, MatPlot


class tkWin(tk.Frame):
    def __init__(self, master: tk.Tk, winTitle: str):
        super().__init__(master)

        self._frmApp: tk.Tk = master
        self._title: str = winTitle
        self._frmApp.title(self._title)

        self._frmApp.protocol("WM_DELETE_WINDOW", self.exit_window)

        # self.__menuDict = {}

    '''
        设置窗口居中和宽高
        :param window: 主窗体
        :param Width: 窗口宽度
        :param Hight: 窗口高度
        :return: 无
    '''
    def __center_window(self, width: int, hight: int):

        # 获取屏幕宽度和高度
        sw = self._frmApp.winfo_screenwidth()
        sh = self._frmApp.winfo_screenheight()

        # 计算中心坐标
        cen_x = (sw - width) / 2
        cen_y = (sh - hight) / 2 * 0.9

        # 设置窗口大小并居中
        self._frmApp.geometry('%dx%d+%d+%d' %(width, hight, cen_x, cen_y))

    def show_err(self, title: str, err: str):
        _ = tkMessageBox.showerror(title, err)

    def show_info(self, title: str, info: str):
        _ = tkMessageBox.showinfo(title, info)

    def exit_window(self):
        res = tkMessageBox.askquestion('Exit Application', 'Do you really want to exit?')
        if res == 'yes':
            self._frmApp.destroy()

    def create_window(self, cfgFile: str):
        elementTree = et.parse(cfgFile)
        winRoot = elementTree.getroot()
        winTitle = winRoot.attrib["Title"]
        width = int(winRoot.attrib["Height"])
        hight = int(winRoot.attrib["Width"])
        self.__center_window(width, hight)

        for frm in list(winRoot):
            tag = frm.tag
            try:
                titleFrm = frm.attrib["title"]
                pv(titleFrm)
            except Exception as r:
                po(f"{tag}: {r}")
                return
            if tag == "LabelFrame":
                frame = tk.LabelFrame(self._frmApp, text=titleFrm)
            elif tag == "Frame":
                frame = tk.Frame(self._frmApp)
            else:
                atrDict = frm.attrib
                self.__create_control(self._frmApp, tag, atrDict)
                continue
            # pv(list(frm))
            po(f"{tag}: {titleFrm}")
            posFrm = frm.attrib["pos"]
            xPadFrm = eval(frm.attrib["xPad"])
            yPadFrm = eval(frm.attrib["yPad"])            
            for control in list(frm):
                tag = control.tag
                atrDict = control.attrib
                self.__create_control(frame, tag, atrDict)

            frame.pack(side=posFrm, fill=tk.BOTH, expand=True, padx=xPadFrm, pady=yPadFrm)

    def __assemble_control(self, ctrl, atrDict):
        layout = atrDict["layout"]
        if layout == "grid":
            row, column = eval(atrDict["pos"])
            ctrl.grid(row=row, column=column, sticky=tk.W)
        elif layout == "pack":
            ctrl.pack(side=atrDict["pos"], fill=tk.BOTH, expand=True, padx=eval(atrDict["xPad"]), pady=eval(atrDict["yPad"]))
        else:
            raise Exception(f"{atrDict['text']}: unknown layout")

    def __create_control(self, frame, tag, atrDict):
        try:
            title = atrDict["title"]
            ctrlName = title.replace(" ", "")
            varTitle = f"_var{title}"
            # pv(varTitle)
        except Exception as r:
            po(f"tag: {tag}, Error: {r}")
            return
        if tag == "MatPlot":
            pos = atrDict["pos"]
            xLabel = atrDict["xLabel"]
            xPad = eval(atrDict["xPad"])
            xAxis: AxisData | Any = AxisData(xLabel, xPad)
            yLabel = atrDict["yLabel"]
            yPad = eval(atrDict["yPad"])
            yAxis = AxisData(yLabel, yPad)
            self.__dict__[f"_{ctrlName}"] = MatPlot(frame, title, pos, xAxis, yAxis)
        elif tag == "Label":
            text = cast(str, atrDict["text"])
            layout = atrDict["layout"]
            ctrl = tk.Label(frame, text=text)
            self.__assemble_control(ctrl, atrDict)
        elif tag == "Entry":
            width = int(atrDict["width"])
            txtTitle = f"_txt{title}"
            # pv(txtTitle)
            self.__dict__[varTitle] = tk.StringVar()
            self.__dict__[txtTitle] = ttk.Entry(frame, textvariable=self.__dict__[varTitle], width=width)
            self.__assemble_control(self.__dict__[txtTitle], atrDict)
        elif tag == "Combobox":
            textvariable = atrDict["textvariable"]
            self.__dict__[f"_{textvariable}"] = tk.StringVar()
            ctrl = ttk.Combobox(frame, textvariable=self.__dict__[f"_{textvariable}"], values=eval(atrDict["values"]), state=atrDict["state"], width=int(atrDict["width"]))
            _ = ctrl.current(int(atrDict["default"]))
            ctrl.bind('<<ComboboxSelected>>', getattr(self, f"_{textvariable}Changed"))
            self.__assemble_control(ctrl, atrDict)
        elif tag == "Radiobutton":
            if varTitle not in self.__dict__:
                self.__dict__[varTitle] = tk.IntVar()
            value = int(atrDict["value"])
            # pv(value)
            # pv(self.__dict__[varTitle])
            ctrl = ttk.Radiobutton(frame, variable=self.__dict__[varTitle], value=int(atrDict["value"]), text=atrDict["text"], command=getattr(self, f"_{title}Changed"))
            # pv(ctrl)
            self.__assemble_control(ctrl, atrDict)
        elif tag == "Button":
            text = atrDict["text"]
            cmdName = f"_btn{text.replace(' ', '')}Click"
            ctrl = ttk.Button(master=frame, text=text, command=getattr(self, cmdName))
            self.__assemble_control(ctrl, atrDict)
            
        else:
            raise Exception(f"{tag}: unknown Control")        

    def config_menu(self, cfgFile: str | None = None):
        menubar = tk.Menu(self._frmApp)

        if cfgFile:
            elementTree = et.parse(cfgFile)
            menuRoot = elementTree.getroot()
            for menuItem in list(menuRoot):
                label = menuItem.attrib["Header"]
                menu = tk.Menu(menubar, tearoff=False)
                for subMenuItm in list(menuItem):
                    try:
                        subLabel = subMenuItm.attrib["Command"]
                        cmdName = subLabel.lower().replace(" ", "_").replace("...", "")
                        if subLabel == "Exit":
                            cmd = self.exit_window
                        else:
                            cmd = getattr(self, f"_{cmdName}")
                    except Exception as r:
                        po(f"tag: {subMenuItm.tag}, error: {r}")

                    try:
                        if subMenuItm.tag == "Separator":
                            menu.add_separator()
                            continue
                        elif subMenuItm.tag == "Checkbutton":
                            varName = subMenuItm.attrib["variable"]
                            self.__dict__[f"_{varName}"] = tk.BooleanVar()
                            var = self.__dict__[f"_{varName}"]
                            var.set(True)
                            menu.add_checkbutton(label=subLabel, command=cmd,
                                variable=var)
                            continue
                        menu.add_command(label=subLabel, command=cmd)
                    except Exception as r:
                        po(f"label: {subLabel}, error: {r}")
                menubar.add_cascade(label=label, menu=menu)
        else:
            fileMenu = tk.Menu(menubar, tearoff=False)
            # fileMenu.add_separator()
            fileMenu.add_command(label="Exit", command=self.exit_window)
            menubar.add_cascade(label="File", menu=fileMenu)

        self._frmApp.config(menu=menubar)

    def _about(self):
        self.show_info(self._title, "haha\nhaa")

if __name__ == '__main__':
    curPath = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        # po("script is packaged!")
        curPath = os.path.dirname(os.path.abspath(sys.executable))

    class App(tkWin):
        def __init__(self, master: tk.Tk, winTitle: str):
            super().__init__(master, winTitle)
        def _export_coefficients(self):
            pass
        def _export_time_domain_data(self):
            pass
        def _export_frequency_domain_data(self):
            pass
        def _info(self):
            pass
        def _Filter_TypeChanged(self):
            pass
        def _Response_PlotChanged(self):
            pass
        def _win_typChanged(self):
            pass
        def _dip_typChanged(self):
            pass
        def _btnDesignFilterClick(self):
            pass

    root = tk.Tk()
    myapp = App(root, "Basic App Example")
    winSampleXml = os.path.join(curPath, 'resources', 'windowSample.xml')
    myapp.create_window(winSampleXml)
    menuSampleXml = os.path.join(curPath, 'resources', 'menuSample.xml')
    myapp.config_menu(menuSampleXml)

    myapp.mainloop()
