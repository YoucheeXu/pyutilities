#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import abc
import xml.etree.ElementTree as et
import tkinter as tk
from typing import Any, TypeAlias
from collections.abc import Callable

try:
    from logit import pv, pe, po
except ImportError:
    from pyutilities.logit import pv, pe, po


# EventHanlder: TypeAlias = Callable[[tuple[Any, ...], dict[str, Any]], Any]
EventHanlder: TypeAlias = Callable[[str, dict[str, Any]], Any]


class Control(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def configure(self, **kwargs):
        pass

    @abc.abstractmethod
    def __getitem__(self, item: str):
        pass

    @abc.abstractmethod
    def __setitem__(self, item: str, value):
        pass

    @abc.abstractmethod
    def disable(self, is_disbl: bool = True):
        pass

    @abc.abstractmethod
    def hide(self, is_hide: bool = True):
        pass

    @abc.abstractmethod
    def destroy(self):
        pass


class MsgLoop:
    def __init__(self):
        self._eventhandler_dict: dict[str, list[EventHanlder]] = {}

    def register_eventhandler(self, idmsg: str, handler: EventHanlder):
        handlerlist = self._eventhandler_dict.get(idmsg)
        if handlerlist is not None:
            self._eventhandler_dict[idmsg].append(handler)
        else:
            self._eventhandler_dict[idmsg] = [handler]

    def process_message(self, idmsg: str, **kwargs: Any):
        funcs = self._eventhandler_dict.get(idmsg, None)
        if funcs is not None:
            ret = None
            for func in funcs:
                ret = func(**kwargs)
            return ret
        po(f"undeal msg of {idctrl}: {kwargs}")


class WinBasic(MsgLoop, metaclass=abc.ABCMeta):
    def __init__(self):
        super().__init__()
        self._x: int = 0
        self._y: int = 0
        self._w: int = 0
        self._h: int = 0
        # self._win: tk.Tk = tk.Tk()
        self._idctrl_dict: dict[str, Control] = {}

    @abc.abstractmethod
    def create_window(self, xmlfile: str):
        pass

    @abc.abstractmethod
    def get_winsize(self) -> tuple[int, int, int, int]:
        pass

    def create_xml(self, tag: str, attr_dict: dict[str, str], root: et.Element | None = None) -> et.Element:
        # try:
        if root is not None:
            item_xml = et.SubElement(root, tag)
        else:
            item_xml = et.Element(tag)
        item_xml.attrib = attr_dict.copy()
        return item_xml
        # except RuntimeError as r:
        #     print(f"\n{tag}:{atr_dict['id']}->errot to create_item: {r}")

    def create_controls(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> list[str]:
        idctrl_list: list[str] = []
        idctrl, ctrl = self.create_control(parent, ctrl_cfg, level)
        idctrl_list.append(idctrl)
        tag = ctrl_cfg.tag
        if tag in ["Menu", "Notebook", "RadiobuttonGroup",
            "Statusbar", "Toolbar", "Dialog"]:
            pass
        else:
            for subctrl_cfg in list(ctrl_cfg):
                subidctrl_list = self.create_controls(ctrl, subctrl_cfg, level + 1)
                idctrl_list.extend(subidctrl_list)
        self.assemble_control(ctrl, ctrl_cfg.attrib, f"{'  '*level}")
        return idctrl_list

    @abc.abstractmethod
    def create_control(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> tuple[str, tk.Misc]:
        pass

    @abc.abstractmethod
    def assemble_control(self, ctrl: tk.Misc, attr_dict: dict[str, str], prefix: str = ""):
        pass

    def delete_control(self, idctrl: str):
        self._idctrl_dict[idctrl].destroy()
        del self._idctrl_dict[idctrl]

    def disable_control(self, ctrl: tk.Misc, is_disbl: bool = True):
        assert isinstance(ctrl, tk.Widget)
        if is_disbl:
            ctrl.configure(state="disabled")
        else:
            ctrl.configure(state="normal")

    def get_control(self, idctrl: str):
        return self._idctrl_dict[idctrl]

    @abc.abstractmethod
    def show_err(self, title: str = "", message: str = ""):
        pass

    @abc.abstractmethod
    def go():
        pass

    # # def process_message(self, idctrl: str, *args: Any, **kwargs: Any):
    # def process_message(self, idmsg: str, **kwargs: Any):
    #     return MsgLoop.process_message(self, idmsg, **kwargs)
