#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import tkinter as tk
import tkinter.messagebox as tkMessageBox
import tkinter.ttk as ttk
# import tkinter.tix as tix

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

try:
    from logit import pv, po
    from matplot import MatPlot
except ImportError:
    from pyutilities.logit import pv
    from pyutilities.matplot import MatPlot

# from PIL import Image, ImageTk	# for imgButton
import PIL
import cv2	# for imgPannel

# https://github.com/xinetzone/tkinter_action/blob/master/app/tools/tips.py
class ToolTip:
    '''针对指定的 widget 创建一个 tooltip
    参考：https://stackoverflow.com/a/36221216
    '''
    def __init__(self, widget, text, timeout=500, offset=(0, 20), **kw):
        '''
        参数
        =======
        widget: tkinter 小部件
        text: (str) tooltip 的文本信息
        timeout: 鼠标必须悬停 timeout 毫秒，才会显示 tooltip
        '''
        # 设置 用户参数
        self.__widget = widget
        self.__text = text
        self.__timeout = timeout
        self.__offset = offset
        # 内部参数初始化
        self.__init_params()
        # 绑定事件
        self.__widget.bind("<Enter>", self.__enter)
        self.__widget.bind("<Leave>", self.__leave)
        self.__widget.bind("<ButtonPress>", self.__leave)
        
    def __init_params(self):
        '''内部参数的初始化'''
        self.__id_after = None
        self.__x, self.__y = 0, 0
        self.__tipwindow = None
        self.__background = 'lightyellow'
        
    def __cursor(self, event):
        '''设定 鼠标光标的位置坐标 (x,y)'''
        self.__x = event.x
        self.__y = event.y
        
    def __unschedule(self):
        '''取消用于鼠标悬停时间的计时器'''
        if self.__id_after:
            self.__widget.after_cancel(self.__id_after)
        else:
            self.__id_after = None

    def __tip_window(self):
        window = tk.Toplevel(self.__widget)
        # 设置窗体属性
        ## 隐藏窗体的标题、状态栏等
        window.overrideredirect(True) 
        ## 保持在主窗口的上面
        window.attributes("-toolwindow", 1)  # 也可以使用 `-topmost`
        window.attributes("-alpha", 0.92857142857)    # 设置透明度为 13/14
        x = self.__widget.winfo_rootx() + self.__x + self.__offset[0]
        y = self.__widget.winfo_rooty() + self.__y + self.__offset[1]
        window.wm_geometry("+%d+%d" % (x, y))
        return window
            
    def __showtip(self):
        """
            创建一个带有工具提示文本的 topoltip 窗口
        """
        params = {
            'text': self.__text, 
            'justify': 'left',
            'background': self.__background,
            'relief': 'solid', 
            'borderwidth': 1
        }
        self.__tipwindow = self.__tip_window()
        label = ttk.Label(self.__tipwindow, **params)
        label.grid(sticky='nsew')
            
    def __schedule(self):
        """
            安排计时器以计时鼠标悬停的时间
        """
        self.__id_after = self.__widget.after(self.__timeout, self.__showtip)
        
    def __enter(self, event):
        """
        鼠标进入 widget 的回调函数
        
        参数
        =========
        :event:  来自于 tkinter，有鼠标的 x,y 坐标属性
        """
        self.__cursor(event)
        self.__schedule()

    def __hidetip(self):
        """
        销毁 tooltip window
        """
        if self.__tipwindow:
            self.__tipwindow.destroy()
        else:
            self.__tipwindow = None
          
    def __leave(self, event):
        """
        鼠标离开 widget 的销毁 tooltip window
         
        参数
        =========
        :event:  来自于 tkinter，没有被使用
        """
        self.__unschedule()
        self.__hidetip()

class Toolbar(tk.Frame):
    def __init__(self, parent, resPath):
        # super().__init__(self.__parent)
        self.__parent = parent
        # tk.Frame.__init__(self, parent)
        super().__init__(self.__parent)
        self.__resPath = resPath
        # self.__tooltip = tix.Balloon(root)

class ImgPanel(tk.Label):
    def __init__(self, parent, text="Image Panel"):
        self.__parent = parent
        # tk.Label.__init__(self, parent)
        super().__init__(self.__parent)
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
        self.__image = image


class tkWin(tk.Frame):
    def __init__(self):
        self._frmApp = tk.Tk()
        super().__init__(self._frmApp)

        self._frmApp.protocol("WM_DELETE_WINDOW", self.exit_window)

        # self.__menuDict = {}

    '''
        设置窗口居中和宽高
        :param window: 主窗体
        :param Width: 窗口宽度
        :param Hight: 窗口高度
        :return: 无
    '''
    def __center_window(self, width, hight):

        # 获取屏幕宽度和高度
        sw = self._frmApp.winfo_screenwidth()
        sh = self._frmApp.winfo_screenheight()

        # 计算中心坐标
        cen_x = (sw - width) / 2
        cen_y = (sh - hight) / 2 * 0.9

        # 设置窗口大小并居中
        self._frmApp.geometry('%dx%d+%d+%d' %(width, hight, cen_x, cen_y))

    def show_err(self, title, err):
        tkMessageBox.showerror(title, err)

    def show_info(self, title, info):
        tkMessageBox.showinfo(title, info)

    def _btnExitApplicationClick(self):	
        self.exit_window()

    def exit_window(self):
        res = tkMessageBox.askquestion('Exit Application', 'Do you really want to exit?')
        if res == 'yes':
            self._frmApp.destroy()

    def create_window(self, cfgFile):
        self.__resPath = os.path.dirname(cfgFile)

        elementTree = et.parse(cfgFile)
        winRoot = elementTree.getroot()
        self._title = winRoot.attrib["Title"]
        width = int(winRoot.attrib["Height"])
        hight = int(winRoot.attrib["Width"])

        self._frmApp.title(self._title)
        self.__center_window(width, hight)

        for frm in list(winRoot):
            frame = self.__create_control(self._frmApp, frm)
            # pv(list(frm))
            tag = frm.tag
            if tag == "Frame" or tag == "LabelFrame":
                for control in list(frm):
                    ctrl = self.__create_control(frame, control)
                    self.__assemble_control(ctrl, control.attrib)

            self.__assemble_control(frame, frm.attrib)

    def __assemble_control(self, ctrl, atrDict):
        # pv(atrDict)
        if (atrDict["layout"] == "pack"):
            layout = "pack"
            ctrl.pack(**(eval(atrDict["pack"])))
        elif (atrDict["layout"] == "grid"):
            ctrl.grid(**(eval(atrDict["grid"])))
        else:
            print(f"unknown layout of {atrDict['text']}:{atrDict['layout']}")

    def __create_control(self, parent, control):
        tag = control.tag
        atrDict = control.attrib
        text = atrDict["text"]
        legalName = text.replace(" ", "")
        print(f"tag: {tag}, text: {text}")
        if tag == "LabelFrame":
            ctrl = tk.LabelFrame(parent, text=text)
        elif tag == "Frame":
            ctrl = tk.Frame(parent)
        elif tag == "MatPlot":
            self.__dict__[f"_{legalName}"] = MatPlot(parent, text, atrDict["xLabel"], atrDict["yLabel"])
            ctrl = self.__dict__[f"_{legalName}"]
        elif tag == "Label":
            ctrl = tk.Label(parent, text=text)
        elif tag == "Entry":
            width = int(atrDict["width"])
            ctrlName = f"_txt{legalName}"
            varText = f"_var{legalName}"
            self.__dict__[varText] = tk.StringVar()
            self.__dict__[ctrlName] = ttk.Entry(parent, textvariable=self.__dict__[varText], width=width)
            ctrl = self.__dict__[ctrlName]
        elif tag == "Combobox":
            varText = f"_var{legalName}"
            self.__dict__[varText] = tk.StringVar()
            ctrl = ttk.Combobox(parent, textvariable=self.__dict__[varText], values=eval(atrDict["values"]), state=atrDict["state"], width=int(atrDict["width"]))
            ctrl.current(int(atrDict["default"]))
            ctrl.bind('<<ComboboxSelected>>', getattr(self, f"{varText}Changed"))
        elif tag == "Radiobutton":
            varText = f"_var{legalName}"
            if varText not in self.__dict__:
                self.__dict__[varText] = tk.IntVar()
            value = int(atrDict["value"])
            ctrl = ttk.Radiobutton(parent, variable=self.__dict__[varText], value=int(atrDict["value"]), text=atrDict["title"], command=getattr(self, f"{varText}Changed"))
        elif tag == "Button":
            cmdName = f"_btn{legalName}Click"
            ctrl = ttk.Button(master=parent, text=text, command=getattr(self, cmdName))
        elif tag == "ImgButton":
            imgFile = os.path.join(self.__resPath, atrDict["img"])
            img = PIL.Image.open(imgFile)
            eimg = PIL.ImageTk.PhotoImage(img)
            cmdName = f"_btn{legalName}Click"
            # ctrl = tix.Button(parent, image=eimg, relief=tk.FLAT, command=getattr(self, cmdName))
            ctrl = tk.Button(parent, image=eimg, relief=tk.FLAT, command=getattr(self, cmdName))
            ctrl.image = eimg
            # self.__tooltip.bind_widget(ctrl, balloonmsg=tooltip)
            tooltip = ToolTip(ctrl, text)		
        elif tag == "Toolbar":
            ctrl = Toolbar(parent, self.__resPath)
            # pv(list(con  trol))
            for subCtrl in list(control):
                imgButton = self.__create_control(ctrl, subCtrl)
                self.__assemble_control(imgButton, subCtrl.attrib)
        elif tag == "ImgPanel":
            ctrlName = f"_panel{legalName}"
            pv(ctrlName)
            self.__dict__[ctrlName] = ImgPanel(parent, text)
            ctrl = self.__dict__[ctrlName]
        else:
            raise Exception(f"{tag}: unknown Control")		

        return ctrl

    def config_menu(self, cfgFile=None):
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
                        print(f"tag: {subMenuItm.tag}, error: {r}")

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
                        print(f"label: {subLabel}, error: {r}")
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
    import os
    import sys

    class App(tkWin):
        def __init__(self):
            super().__init__()
        def _export_coefficients(self):
            pass
        def _export_time_domain_data(self):
            pass
        def _export_frequency_domain_data(self):
            pass
        def _info(self):
            pass
        def _varWindowTypeChanged(self):
            pass
        def _varFilterTypeChanged(self):
            pass
        def _varImpulseChanged(self):
            pass
        def _varStepChanged(self):
            pass
        def _varResponsePlotChanged(self):
            pass
        def _varDisplayTypeChanged(self):
            pass
        def _btnDesignFilterClick(self):
            pass

    curPath = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        # po("script is packaged!")
        curPath = os.path.dirname(os.path.abspath(sys.executable))
    myapp = App()
    winSampleXml = os.path.join(curPath, 'resources', 'windowSample.xml')
    myapp.create_window(winSampleXml)
    menuSampleXml = os.path.join(curPath, 'resources', 'menuSample.xml')
    myapp.config_menu(menuSampleXml)
    myapp.mainloop()
