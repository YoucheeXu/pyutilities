#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import TypeVar, Callable, Generic, cast
import threading

# 定义线程锁
single_lock = threading.Lock()

# 定义泛型类型变量，添加协变标记以增强类型兼容性
T = TypeVar('T', covariant=True)


class SingletonWrapper(Generic[T]):
    """单例装饰器的泛型包装类，自适应处理构造函数参数"""
    cls: type[T]
    _instances: dict[type[T], T]
    __wrapped__: type[T]  # 显式声明__wrapped__属性的类型

    def __init__(self, cls: type[T]) -> None:
        """初始化包装器，接收被装饰的类"""
        self.cls = cls
        self._instances = {}
        self.__wrapped__ = cls

    def __call__(self, *args: object, **kwargs: object) -> T:
        """控制类的实例化过程，确保全局唯一实例"""
        with single_lock:
            if self.cls not in self._instances:
                # 动态传递参数，无参数时不传递任何值
                self._instances[self.cls] = self.cls(*args, **kwargs)
        return self._instances[self.cls]


# @overload
# def singleton(cls: type[T]) -> Callable[..., T]: ...


def singleton(cls: type[T]) -> Callable[..., T]:
    """ 单例模式装饰器
    用于装饰需要全局唯一实例的类，确保类在程序生命周期内
    只被实例化一次，后续调用都返回同一个实例。

    Args:
        cls: 要被装饰的类
        
    Returns:
        包装后的可调用对象
    """
    # return SingletonWrapper[T](cls)
    wrapper = SingletonWrapper[T](cls)
    
    # 保留原始类的元数据，帮助类型检查器识别
    wrapper.__wrapped__ = cls

    # 强制类型转换，明确告诉类型检查器返回类型
    return cast(type[T], wrapper)
