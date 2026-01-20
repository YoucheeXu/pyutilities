#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
from types import ModuleType
from typing import Final, Callable

from src.pyutilities.singleton import singleton


@singleton
class _const(ModuleType):
    """ 单例模式的常量管理模块

    特性：
    - 常量名称必须全大写（强制命名规范）
    - 常量一旦定义不可修改或删除（只读特性）
    - 全局唯一实例，确保常量在整个程序中保持一致
    """
    
    class ConstError(PermissionError):
        """尝试修改或删除已定义常量时触发的异常"""
        pass

    class ConstCaseError(TypeError):
        """常量名称不是全大写时触发的异常"""
        pass

    def __init__(self, module_name: str | None = None) -> None:
        """初始化常量模块，继承ModuleType的特性"""
        # 确定模块名称，默认使用当前模块名
        name = module_name if module_name is not None else __name__
        super().__init__(name)
        
        # 初始化内置属性（标记为"内置"，清空时保留）
        self.__dict__["__version__"] = "1.0.0"
        self.__dict__["__description__"] = "A singleton-based constant management module"
        # 手动绑定模块原生属性（解决coverage访问__file__的问题）
        self.__dict__["__file__"] = sys.modules[name].__file__ if name in sys.modules else __file__
        self.__dict__["__name__"] = name

    def __setattr__(self, name: str, value: object) -> None:
        """ 重写属性设置方法，实现常量约束：
        1. 已存在的常量不允许重新赋值
        2. 常量名称必须使用全大写字母
        """
        # 跳过内置特殊属性的设置（避免覆盖__file__等）
        if name.startswith("__") and name.endswith("__"):
            self.__dict__[name] = value
            return
        # 校验1：不允许重复赋值（已存在则报错）
        if name in self.__dict__:
            raise self.ConstError(f"Cannot modify constant '{name}': constants are immutable")
        # 校验2：名称必须全大写
        if not name.isupper():
            raise self.ConstCaseError(f"Constant name '{name}' must be in uppercase")
        # 合法常量：添加到字典
        self.__dict__[name] = value

    def __delattr__(self, name: str) -> None:
        """重写属性删除方法，禁止删除已定义的常量"""
        # 跳过内置特殊属性的设置（避免覆盖__file__等）
        if name.startswith("__") and name.endswith("__"):
            raise self.ConstError(f"Cannot delete built-in attribute '{name}'")
        if name in self.__dict__:
            raise self.ConstError(f"Cannot delete constant '{name}': constants cannot be deleted")
        raise NameError(f"Constant '{name}' is not defined")

    def __getattr__(self, name: str) -> object:
        """获取属性：内置属性正常返回，未定义常量抛异常"""
        if name.startswith("__") and name.endswith("__"):
            return super().__getattribute__(name)
        if name not in self.__dict__:
            raise NameError(f"Constant '{name}' is not defined")
        return self.__dict__[name]

    def list_constants(self) -> list[str]:
        """返回所有用户定义的常量名称（排除模块内置属性）"""
        return [
            name for name in sorted(self.__dict__.keys())
            if name.isupper() and not name.startswith("__")
        ]

    def get_constant(self, name: str) -> object | None:
        """安全获取常量值，不存在时返回None而非抛出异常"""
        return self.__dict__.get(name)

    def clear_user_constants(self) -> None:
        """彻底清空所有用户常量（保留内置属性）"""
        # 遍历并删除所有用户定义的常量（全大写、非双下划线）
        for name in list(self.__dict__.keys()):  # 转列表避免遍历中修改字典
            if name.isupper() and not name.startswith("__"):
                del self.__dict__[name]


# 替换模块为单例实例（全局唯一）
sys.modules[__name__] = _const(__name__)


# 导出公共接口
__all__ = ["ConstError", "ConstCaseError", "list_constants", "get_constant", "clear_user_constants"]

# 为公共接口添加Final类型提示，明确其不可修改性，绑定模块级接口
list_constants: Final[Callable[[], list[str]]] = sys.modules[__name__].list_constants
get_constant: Final[Callable[[str], object | None]] = sys.modules[__name__].get_constant
ConstError: Final[type[PermissionError]] = sys.modules[__name__].ConstError
ConstCaseError: Final[type[TypeError]] = sys.modules[__name__].ConstCaseError
