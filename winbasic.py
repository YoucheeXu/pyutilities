#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import abc
import xml.etree.ElementTree as et
import tkinter as tk
from typing import Any, TypeAlias
from collections.abc import Callable

# EventHanlder: TypeAlias = Callable[[tuple[Any, ...], dict[str, Any]], Any]
EventHanlder: TypeAlias = Callable[[str, dict[str, Any]], Any]


class Control(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def configure(self, **kwargs):
        pass

    @abc.abstractmethod
    def get_winsize(self) -> tuple[int, int, int, int]:
        pass

    @abc.abstractmethod
    def show(self, is_show: bool = True):
        pass

    @abc.abstractmethod
    def disable(self, is_disbl: bool = True):
        pass

    @abc.abstractmethod
    def destory(self):
        pass


class WinBasic(abc.ABC):
    def __init__(self):
        self._x: int = 0
        self._y: int = 0
        self._w: int = 0
        self._h: int = 0
        # self._win: tk.Tk = tk.Tk()

    @abc.abstractmethod
    def get_winsize(self) -> tuple[int, int, int, int]:
        pass

    @abc.abstractmethod
    def create_xml(self, tag: str, attr_dict: dict[str, str], root: et.Element | None = None) -> et.Element:
        pass

    @abc.abstractmethod
    def create_controls(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> list[str]:
        pass

    @abc.abstractmethod
    def create_control(self, parent: tk.Misc, ctrl_cfg: et.Element, level: int = 0) -> tuple[str, tk.Misc]:
        pass

    @abc.abstractmethod
    def assemble_control(self, ctrl: tk.Misc, attr_dict: dict[str, str], prefix: str = ""):
        pass

    @abc.abstractmethod
    def delete_control(self, idctrl: str):
        pass

    @abc.abstractmethod
    def disable_control(self, ctrl: tk.Misc, is_disbl: bool = True):
        pass

    @abc.abstractmethod
    def get_control(self, idctrl: str) -> tk.Misc:
        pass

    @abc.abstractmethod
    def show_err(self, title: str = "", message: str = ""):
        pass

    @abc.abstractmethod
    def register_eventhandler(self, idctrl: str, handler: EventHanlder):
        pass

    @abc.abstractmethod
    # def process_message(self, idctrl: str, *args: Any, **kwargs: Any):
    def process_message(self, idctrl: str, **kwargs: Any):
        pass
