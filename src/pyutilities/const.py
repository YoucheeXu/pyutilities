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
        
        # 初始化模块元信息（内置常量）
        self.__dict__["__version__"] = "1.0.0"
        self.__dict__["__description__"] = "A singleton-based constant management module"

    def __setattr__(self, name: str, value: object) -> None:
        """ 重写属性设置方法，实现常量约束：
        1. 已存在的常量不允许重新赋值
        2. 常量名称必须使用全大写字母
        """
        if name in self.__dict__:
            raise self.ConstError(f"Cannot modify constant '{name}': constants are immutable")
        if not name.isupper():
            raise self.ConstCaseError(f"Constant name '{name}' must be in uppercase")
        self.__dict__[name] = value

    def __delattr__(self, name: str) -> None:
        """重写属性删除方法，禁止删除已定义的常量"""
        if name in self.__dict__:
            raise self.ConstError(f"Cannot delete constant '{name}': constants cannot be deleted")
        raise NameError(f"Constant '{name}' is not defined")

    def __getattr__(self, name: str) -> object:
        """获取常量时提供友好的错误提示"""
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


# 将当前模块替换为_const单例实例，实现全局常量功能
sys.modules[__name__] = _const()


# 类型声明，增强类型提示和自动补全
__all__ = ["ConstError", "ConstCaseError", "list_constants", "get_constant"]

# 为公共接口添加Final类型提示，明确其不可修改性
list_constants: Final[Callable[[], list[str]]] = sys.modules[__name__].list_constants
get_constant: Final[Callable[[str], object | None]] = sys.modules[__name__].get_constant
ConstError: Final[type[PermissionError]] = sys.modules[__name__].ConstError
ConstCaseError: Final[type[TypeError]] = sys.modules[__name__].ConstCaseError
