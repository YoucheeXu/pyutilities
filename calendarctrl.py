#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
import calendar
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import datetime

try:
    from logit import pv, pe
except ImportError:
    from pyutilities.logit import pv, pe


class CalendarCtrl:
    def __init__(self, point: tuple[int, int] | None = None):
        self._master: tk.Toplevel = tk.Toplevel()
        self._master.withdraw()
        # fwday = calendar.SUNDAY
        fwday = 6
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        locale = None
        sel_bg = '#ecffc4'
        sel_fg = '#05640e'
        self._date: datetime.date = datetime.datetime(year, month, 1)        # 每月第一日
        self._selection: tuple[str, str, str] | None = None     # 设置为未选中日期
        self.G_Frame: ttk.Frame = ttk.Frame(self._master)
        self._cal: calendar.TextCalendar | calendar.LocaleTextCalendar = \
            self.__get_calendar(locale, fwday)
        self.__setup_styles()        # 创建自定义样式
        self.__place_widgets()         # pack/grid小部件
        self.__config_calendar()     # 调整日历列和安装标记
        self._canvas_text: int = 0
        self._font: tkFont.Font = tkFont.Font()
        # 配置画布和正确的绑定，以选择日期。
        self._canvas: tk.Canvas = self.__setup_selection(sel_bg, sel_fg)
        # 存储项ID，用于稍后插入。
        self._items: list[str] = [self._calendar.insert('', 'end', values=[]) for _ in range(6)]
        # 在当前空日历中插入日期
        self._update()
        self.G_Frame.pack(expand = 1, fill = 'both')
        self._master.overrideredirect(True)
        self._master.update_idletasks()
        width, height = self._master.winfo_reqwidth(), self._master.winfo_reqheight()
        self.height: int = height
        if point:
            x, y = point[0], point[1]
        else:
            x, y = (self._master.winfo_screenwidth() - width)/2, \
                (self._master.winfo_screenheight() - height)/2
        # self._master.geometry('%dx%d+%d+%d' % (width, height, x, y)) # 窗口位置居中
        self._master.geometry(f"{width}x{height}+{x}+{y}") # 窗口位置居中
        _ = self._master.after(300, self._main_judge)
        self._master.attributes('-topmost', True)
        self._master.grab_set()        # ensure all input goes to our window
        self._master.deiconify()
        self._master.focus_set()
        self._master.wait_window()

    def __get_calendar(self, locale: tuple[str | None, str | None] | None = None,
            fwday: int = 0):
        if locale is None:
            return calendar.TextCalendar(fwday)
        else:
            return calendar.LocaleTextCalendar(fwday, locale)

    def __setitem__(self, item: str, value):
        if item in ('year', 'month'):
            raise AttributeError("attribute '%s' is not writeable" % item)
        elif item == 'selectbackground':
            self._canvas['background'] = value
        elif item == 'selectforeground':
            _ = self._canvas.itemconfigure(self._canvas_text, item=value)
        else:
            self.G_Frame.__setitem__(item, value)

    def __getitem__(self, item: str):
        if item in ('year', 'month'):
            return getattr(self._date, item)
        elif item == 'selectbackground':
            return self._canvas['background']
        elif item == 'selectforeground':
            return self._canvas.itemcget(self._self._canvas_text, 'fill')
        else:
            r = ttk.tclobjs_to_py({item: ttk.Frame.__getitem__(self, item)})
            return r[item]

    def __setup_styles(self):
        # 自定义TTK风格
        style = ttk.Style(self._master)
        arrow_layout = lambda dir: (
            [('Button.focus', {'children': [('Button.%sarrow' % dir, None)]})]
        )
        style.layout('L.TButton', arrow_layout('left'))
        style.layout('R.TButton', arrow_layout('right'))

    def __place_widgets(self):
        # 标头框架及其小部件
        input_judgment_num = self._master.register(self.input_judgment) # 需要将函数包装一下，必要的
        hframe = ttk.Frame(self.G_Frame)
        gframe = ttk.Frame(self.G_Frame)
        bframe = ttk.Frame(self.G_Frame)
        hframe.pack(in_=self.G_Frame, side='top', pady=5, anchor='center')
        gframe.pack(in_=self.G_Frame, fill=tk.X, pady=5)
        bframe.pack(in_=self.G_Frame, side='bottom', pady=5)
        lbtn = ttk.Button(hframe, style='L.TButton', command=self._prev_month)
        lbtn.grid(in_=hframe, column=0, row=0, padx=12)
        rbtn = ttk.Button(hframe, style='R.TButton', command=self._next_month)
        rbtn.grid(in_=hframe, column=5, row=0, padx=12)
        self._cmb_year: ttk.Combobox = ttk.Combobox(hframe, width=5,
            values=[str(year) for year in range(datetime.datetime.now().year,
                datetime.datetime.now().year-11, -1)],
            validate='key', validatecommand=(input_judgment_num, '%P'))
        _ = self._cmb_year.current(0)
        self._cmb_year.grid(in_=hframe, column=1, row=0)
        _ = self._cmb_year.bind('<KeyPress>', lambda event: self._update(event, True))
        _ = self._cmb_year.bind("<<ComboboxSelected>>", self._update)
        tk.Label(hframe, text = '年', justify = 'left').grid(in_=hframe, column=2, row=0, padx=(0,5))
        self._cmb_month: ttk.Combobox = ttk.Combobox(hframe, width=3,
            values=['%02d' % month for month in range(1,13)], state='readonly')
        _ = self._cmb_month.current(datetime.datetime.now().month - 1)
        self._cmb_month.grid(in_=hframe, column=3, row=0)
        _ = self._cmb_month.bind("<<ComboboxSelected>>", self._update)
        tk.Label(hframe, text='月', justify='left').grid(in_=hframe, column=4, row=0)
        # 日历部件
        self._calendar: ttk.Treeview = ttk.Treeview(gframe, show='', selectmode='none', height=7)
        self._calendar.pack(expand=1, fill='both', side='bottom', padx=5)
        ttk.Button(bframe, text="确 定", width=6,
            command=lambda: self._exit(True)).grid(row=0, column=0, sticky='ns', padx=20)
        ttk.Button(bframe, text="取 消", width=6, command=self._exit). \
            grid(row=0, column=1, sticky='ne', padx=20)
        tk.Frame(self.G_Frame, bg='#565656').\
            place(x=0, y=0, relx=0, rely=0, relwidth=1, relheigh=2/200)
        tk.Frame(self.G_Frame, bg='#565656'). \
            place(x=0, y=0, relx=0, rely=198/200, relwidth=1, relheigh=2/200)
        tk.Frame(self.G_Frame, bg='#565656'). \
            place(x=0, y=0, relx=0, rely=0, relwidth=2/200, relheigh=1)
        tk.Frame(self.G_Frame, bg='#565656'). \
            place(x=0, y=0, relx=198/200, rely=0, relwidth=2/200, relheigh=1)

    def __config_calendar(self):
        # cols = self._cal.formatweekheader(3).split()
        cols = ['日','一','二','三','四','五','六']
        self._calendar['columns'] = cols
        _ = self._calendar.tag_configure('header', background='grey90')
        _ = self._calendar.insert('', 'end', values=cols, tags='header')
        # 调整其列宽
        font = tkFont.Font()
        maxwidth = max(font.measure(col) for col in cols)
        for col in cols:
            _ = self._calendar.column(col, width=maxwidth, minwidth=maxwidth,
            anchor='center')

    def __setup_selection(self, sel_bg: str, sel_fg: str):
        def __canvas_forget(_: tk.Event[tk.Canvas] | tk.Event[ttk.Treeview]):
            canvas.place_forget()
            self._selection = None

        canvas = tk.Canvas(self._calendar, background=sel_bg,
            borderwidth=0, highlightthickness=0)
        self._canvas_text = canvas.create_text(0, 0, fill=sel_fg, anchor='w')
        _ = canvas.bind('<Button-1>', __canvas_forget)
        _ = self._calendar.bind('<Configure>', __canvas_forget)
        _ = self._calendar.bind('<Button-1>', self._clicked)
        return canvas

    def _build_calendar(self):
        year, month = self._date.year, self._date.month
        # header = self._cal.formatmonthname(year, month, 0)
        # 更新日历显示的日期
        cal = self._cal.monthdayscalendar(year, month)
        for indx, item in enumerate(self._items):
            week = cal[indx] if indx < len(cal) else []
            fmt_week = [('%02d' % day) if day else '' for day in week]
            self._calendar.item(item, values=fmt_week)

    def _show_select(self, text: str, bbox: tuple[int, int, int, int]):
        x, y, width, height = bbox
        textw = self._font.measure(text)
        canvas = self._canvas
        _ = canvas.configure(width=width, height=height)
        canvas.coords(self._canvas_text, (width - textw)/2, height / 2 - 1)
        _ = canvas.itemconfigure(self._canvas_text, text=text)
        canvas.place(in_=self._calendar, x=x, y=y)

    def _clicked(self, evt: tk.Event[ttk.Treeview] | None = None,
            item: str | None = None, column: str | None = None, widget: ttk.Treeview | None = None):
        """ 在日历的某个地方点击"""
        if evt and not item:
            x, y, widget = evt.x, evt.y, evt.widget
            item = widget.identify_row(y)
            column = widget.identify_column(x)
        if not column or item not in self._items:
            # 在工作日行中单击或仅在列外单击。
            return
        assert(widget is not None)
        item_values = widget.item(item)['values']
        if not len(item_values): # 这个月的行是空的。
            return
        text = item_values[int(column[1]) - 1]
        if not text: 
            return
        bbox = widget.bbox(item, column)
        if not bbox: # 日历尚不可见
            _ = self._master.after(20, lambda: self._clicked(None, item, column, widget))
            return
        text = '%02d' % text
        self._selection = (text, item, column)
        self._show_select(text, bbox)

    def _prev_month(self):
        """ 更新日历以显示前一个月"""
        self._canvas.place_forget()
        self._selection = None
        self._date = self._date - datetime.timedelta(days=1)
        self._date = datetime.datetime(self._date.year, self._date.month, 1)
        self._cmb_year.set(self._date.year)
        self._cmb_month.set(self._date.month)
        self._update()

    def _next_month(self):
        """ 更新日历以显示下一个月"""
        self._canvas.place_forget()
        self._selection = None

        year, month = self._date.year, self._date.month
        self._date = self._date + datetime.timedelta(
            days=calendar.monthrange(year, month)[1] + 1)
        self._date = datetime.datetime(self._date.year, self._date.month, 1)
        self._cmb_year.set(self._date.year)
        self._cmb_month.set(self._date.month)
        self._update()

    def _update(self, event: tk.Event[ttk.Combobox] | None = None, key: bool = False):
        """ 刷新界面"""
        if key and event and event.keysym != 'Return':
            return
        year = int(self._cmb_year.get())
        month = int(self._cmb_month.get())
        if year == 0 or year > 9999:
            return
        self._canvas.place_forget()
        self._date = datetime.datetime(year, month, 1)
        self._build_calendar() # 重建日历
        if year == datetime.datetime.now().year and month == datetime.datetime.now().month:
            day = datetime.datetime.now().day
            for _item, day_list in enumerate(self._cal.monthdayscalendar(year, month)):
                if day in day_list:
                    item = 'I00' + str(_item + 2)
                    column = '#' + str(day_list.index(day)+1)
                    _ = self._master.after(100, lambda :self._clicked(item=item, column=column,
                        widget=self._calendar))

    def _exit(self, confirm: bool = False):
        # pv(self._selection)
        if not confirm:
            self._selection = None
        self._master.grab_release()
        self._master.destroy()

    def _main_judge(self):
        """ 判断窗口是否在最顶层"""
        try:
            if self._master.focus_displayof() is None \
                or 'toplevel' not in str(self._master.focus_displayof()):
                self._exit()
            else:
                _ = self._master.after(10, self._main_judge)
        except:
            _ = self._master.after(10, self._main_judge)

    def get_datestr(self):
        """ 返回表示当前选定日期的日期时间"""
        if not self._selection:
            print("no selection")
            return None
        year, month = self._date.year, self._date.month
        pv(year)
        pv(month)
        return str(datetime.datetime(year, month, int(self._selection[0])))[:10]

    def input_judgment(self, content: str):
        """ 输入判断"""
        if content.isdigit() or content == "":
            return True
        else:
            return False


if __name__ == "__main__":
    class CalendarCtrl_test():
        def __init__(self):

            self.root: tk.Tk = tk.Tk()

            # 设置tk窗口在屏幕中心显示
            sw = self.root.winfo_screenwidth()    # 得到屏幕宽度
            sh = self.root.winfo_screenheight()    # 得到屏幕高度
            ww = 200    # 设置窗口 宽度
            wh = 60    # 设置窗口 高度

            x = (sw - ww) / 2
            y = (sh - wh) / 2
            self.root.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

            self.Frame_row1: tk.Frame = tk.Frame(self.root)
            self.Frame_row1.pack()

            self.var_test: tk.StringVar = tk.StringVar()
            self.Entry_test: tk.Entry = tk.Entry(self.Frame_row1, width=10,
                textvariable=self.var_test, font="宋体, 12",
                                         justify='center', )
            self.Entry_test.grid(row=0, column=0, padx=5, pady=5)

            self.Button_test: tk.Button = tk.Button(self.Frame_row1, width=2,
                text='*', font="宋体, 12",
                justify='center',
                command=lambda: self.get_date(self.Entry_test.winfo_rootx(),
                                    self.Entry_test.winfo_rooty() + 20))
            self.Button_test.grid(row=0, column=1, padx=5, pady=5)

            self.root.mainloop()

        def get_date(self, x: int, y: int):    # x, y位Entry的坐标位置
            # 接收弹窗的数据
            res = self.ask_date(x, y)
            if res is None:
                return
            self.var_test.set(res)

        def ask_date(self, x: int, y: int):
            calendar = CalendarCtrl((x, y))
            return calendar.get_datestr()

    app = CalendarCtrl_test()
