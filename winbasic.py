#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import abc
import xml.etree.ElementTree as et
from typing import cast, Literal, Protocol, override
# from typing import TypeAlias
# from collections.abc import Callable, Mapping
from collections import OrderedDict

try:
    from logit import pv, pe, po
except ImportError:
    from pyutilities.logit import pv, pe, po

# EventHanlder: TypeAlias = Callable[[tuple[Any, ...], dict[str, Any]], Any]
# EventHanlder: TypeAlias = Callable[[dict[str, Any]], Any]
# EventHanlder: TypeAlias = Callable[[Mapping[str, Any]], Any]
class EventHanlder(Protocol):
    def __call__(self, **kwargs: object) -> object: ...


# EventsHanlder: TypeAlias = Callable[[str, dict[str, Any]], Any]
# EventsHanlder: TypeAlias = Callable[[str, Mapping[str, Any]], Any]
class EventsHanlder(Protocol):
    def __call__(self, idmsg: str, **kwargs: object) -> object: ...


class Widget:
    def __init__(self):
        pass

    # @abc.abstractmethod
    # def process_message(self, idmsg: str, **kwargs: object) -> object:
        # pass


class Control(Widget, metaclass=abc.ABCMeta):
    def __init__(self, title: str, idself: str):
        super().__init__()
        self._title: str = title
        self._idself: str = idself
        self._backed: bool = True

    @property
    def title(self):
        return self._title

    @property
    def backed(self):
        return self._backed

    def back(self, bset: bool = True):
        self._backed = bset

    @abc.abstractmethod
    def configure(self, **kwargs: object):
        pass

    @abc.abstractmethod
    def __getitem__(self, item: str):
        pass

    @abc.abstractmethod
    def __setitem__(self, item: str, value: object):
        pass

    @abc.abstractmethod
    def hide(self, is_hide: bool = True):
        pass

    def show(self):
        self.hide(False)

    @abc.abstractmethod
    def disable(self, is_disbl: bool = True):
        pass

    def enable(self):
        self.disable(False)

    @abc.abstractmethod
    def destroy(self):
        pass


class Dialog(Widget, metaclass=abc.ABCMeta):
    def __init__(self, title: str, width: int, height: int):
        super().__init__()
        self._xx: int = 0
        self._yy: int = 0
        self._title: str = title
        self._ww: int = width
        self._hh: int = height
        self._backed: bool = True
        self._idctrl_dict: OrderedDict[str, Widget] = OrderedDict()
        self._eventhandler_dict: dict[str, list[EventHanlder]] = {}
        self._msgs_hanlders: list[tuple[int, list[str], EventsHanlder]] = []

    @property
    def title(self):
        return self._title

    def set_title(self, val: str):
        self._title = val

    @property
    def pos(self):
        return self._xx, self._yy

    @property
    def size(self):
        return self._ww, self._hh

    @property
    def backed(self):
        return self._backed

    def back(self, bset: bool = True):
        for idctrl, ctrl in self._idctrl_dict.items():
            try:
                ctrl = cast(Control, ctrl).back(bset)
            except AttributeError as _:
                po(f"{idctrl} doesn't support back")
        self._backed = bset

    def register_eventhandler(self, idmsg: str, handler: EventHanlder):
        handlerlist = self._eventhandler_dict.get(idmsg)
        if handlerlist is not None:
            self._eventhandler_dict[idmsg].append(handler)
        else:
            self._eventhandler_dict[idmsg] = [handler]

    def filter_message(self, hanlder: EventsHanlder,
            typ: Literal[-1, 0, 1] = 0, msglst: list[str] | None = None):
        """filter message to deal with

        Args:
            typ ():
                1: filter all message in msglst
                0: all message
                -1: filter any message except in msglst
            msglst(): message list
            hanlder (): hanlder to deal message

        Returns:
            Any: the result.

        Raises:
            ValueError: If `param1` is equal to `param2`.
        """
        if msglst is not None:
            self._msgs_hanlders.append((typ, msglst, hanlder))
        else:
            self._msgs_hanlders.append((typ, [], hanlder))

    def process_message(self, idmsg: str, **kwargs: object):
        for typ, msglst, hander in self._msgs_hanlders:
            if typ == 0:
                ret = hander(idmsg, **kwargs)
                if ret is not None:
                    return ret
            elif typ == 1:
                if idmsg in msglst:
                    ret = hander(idmsg, **kwargs)
                    if ret is not None:
                        return ret
            elif typ == -1:
                if idmsg not in msglst:
                    ret = hander(idmsg, **kwargs)
                    if ret is not None:
                        return ret

        funcs = self._eventhandler_dict.get(idmsg, None)
        if funcs is not None:
            ret = None
            for func in funcs:
                ret = func(**kwargs)
            return ret

        po(f"undeal msg of {idmsg}: {kwargs}")

    @abc.abstractmethod
    def destroy(self, **kwargs: object):
        # self._eventhandler_dict.clear()
        # self._eventhandler_dict = {}
        # self._msgs_hanlders.clear()
        # self._msgs_hanlders = []
        pass


class WinBasic(Dialog, metaclass=abc.ABCMeta):
    def __init__(self, xmlfile: str):
        element_tree = et.parse(xmlfile)
        self._wincfg: et.Element[str] = element_tree.getroot()
        win_attr = self._wincfg.attrib
        if "Width" in win_attr:
            w, h = int(win_attr["Width"]), int(win_attr["Height"])
        else:
            w, h = 0, 0
        Dialog.__init__(self, win_attr["Title"], w, h)
        # self._idctrl_dict: dict[str, object] = {}
        # self._idctrl_dict: OrderedDict[str, object] = OrderedDict()

    @abc.abstractmethod
    def create_window(self):
        pass

    def create_xml(self, tag: str, attr_dict: dict[str, str], root: et.Element | None = None) -> et.Element:
        if root is not None:
            item_xml = et.SubElement(root, tag)
        else:
            item_xml = et.Element(tag)
        item_xml.attrib = attr_dict.copy()
        return item_xml

    @abc.abstractmethod
    def create_control(self, parent: Widget, ctrl_cfg: et.Element,
            level: int = 0, owner: Dialog | None = None) -> tuple[str, Widget]:
        pass

    @abc.abstractmethod
    def assemble_control(self, ctrl: Widget, attr_dict: dict[str, str], prefix: str = ""):
        pass

    def create_controls(self, parent: Widget, ctrl_cfg: et.Element,
            level: int = 0, owner: Dialog | None = None) -> OrderedDict[str, Widget]:
        idctrl_dict: OrderedDict[str, Widget] = OrderedDict()
        idctrl, ctrl = self.create_control(parent, ctrl_cfg, level, owner)
        idctrl_dict[idctrl] = ctrl
        tag = ctrl_cfg.tag
        if tag in ["Menu", "Notebook", "RadiobuttonGroup",
            "Statusbar", "Toolbar", "Dialog"]:
            pass
        else:
            for subctrl_cfg in list(ctrl_cfg):
                subidctrl_dict = self.create_controls(ctrl, subctrl_cfg, level + 1, owner)
                idctrl_dict.update(subidctrl_dict)
        self.assemble_control(ctrl, ctrl_cfg.attrib, f"{'  '*level}")
        return idctrl_dict

    def delete_control(self, idctrl: str):
        # if idctrl in self._idctrl_dict:
        ctrl = cast(Control, self._idctrl_dict[idctrl])
        ctrl.destroy()
        del self._idctrl_dict[idctrl]

    def get_control(self, idctrl: str):
        return self._idctrl_dict[idctrl]

    @abc.abstractmethod
    def show_err(self, title: str = "", message: str = ""):
        pass

    @abc.abstractmethod
    def go(self):
        pass

    @override
    def destroy(self, **kwargs: object):
        # pv(self._idctrl_dict.keys())
        for idctrl in reversed(list(self._idctrl_dict.keys())):
            if idctrl in self._idctrl_dict:
                # po(f"Going to delete {idctrl}")
                self.delete_control(idctrl)
        self._idctrl_dict.clear()

        super().destroy(**kwargs)
