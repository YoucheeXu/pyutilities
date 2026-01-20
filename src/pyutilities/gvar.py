#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
from types import ModuleType
from typing import Final, Callable, override, cast

from src.pyutilities.singleton import singleton

@singleton
class GlobalVarModule(ModuleType):
    """
    单例模式的全局变量管理模块
    特性：
    1. 全局唯一实例，跨模块共享变量
    2. 支持安全获取变量（不存在返回None）
    3. 支持列出所有全局变量
    4. 支持清空全局变量（主要用于测试）
    5. 可选只读变量保护
    """
    # 内置只读变量（不可修改/删除）
    _READ_ONLY_KEYS: Final[list[str]] = ["ver"]
    
    def __init__(self, module_name: str = __name__) -> None:
        """初始化全局变量模块，继承ModuleType以兼容模块特性"""
        super().__init__(module_name)
        # 初始化内置版本号（只读）
        self.__dict__["ver"] = "0.1.0"
        # 模块元信息
        self.__dict__["__description__"] = "Singleton-based global variable manager"

    @override
    def __setattr__(self, name: str, value: object) -> None:
        """重写属性设置：保护只读变量"""
        # 保护内置只读变量
        if name in self._READ_ONLY_KEYS and name in self.__dict__:
            raise PermissionError(f"Read-only variable '{name}' cannot be modified")
        self.__dict__[name] = value

    @override
    def __delattr__(self, name: str) -> None:
        """重写属性删除：保护只读变量"""
        if name in self._READ_ONLY_KEYS:
            raise PermissionError(f"Read-only variable '{name}' cannot be deleted")
        if name not in self.__dict__:
            raise NameError(f"Global variable '{name}' does not exist")
        del self.__dict__[name]

    def get_var(self, name: str, default: object = None):
        """
        安全获取全局变量
        Args:
            name: 变量名
            default: 不存在时的默认值（默认None）
        Returns:
            变量值或默认值
        """
        return cast(object, self.__dict__.get(name, default))

    def list_vars(self):
        """返回所有用户定义的全局变量（排除内置属性）"""
        return [
            name for name in sorted(self.__dict__.keys())
            if not name.startswith("__") and name not in self._READ_ONLY_KEYS
        ]

    def list_all_vars(self):
        """返回所有变量（包含内置/只读变量）"""
        return sorted(self.__dict__.keys())

    def clear_vars(self):
        """清空所有非只读的全局变量（仅用于测试/重置）"""
        for name in self.list_vars():
            del self.__dict__[name]

# 将模块替换为单例实例，实现全局唯一
sys.modules[__name__] = GlobalVarModule(__name__)

# 导出公共接口（增强类型提示）
__all__ = ["get_var", "list_vars", "list_all_vars", "clear_vars"]

# 绑定模块级接口（适配直接调用）
get_var: Final[Callable[[str, object | None], object | None]] = sys.modules[__name__].get_var
list_vars: Final[Callable[[], list[str]]] = sys.modules[__name__].list_vars
list_all_vars: Final[Callable[[], list[str]]] = sys.modules[__name__].list_all_vars
clear_vars: Final[Callable[[], None]] = sys.modules[__name__].clear_vars
