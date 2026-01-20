#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import TypeVar, Callable, Generic, cast
import threading


# 定义泛型类型变量，添加协变标记以增强类型兼容性
T = TypeVar('T', covariant=True)


class SingletonWrapper(Generic[T]):
    """单例装饰器的泛型包装类，自适应处理构造函数参数"""
    # 类级实例字典，全局唯一
    _instances: dict[type[T], T] = {}
    # 类级锁（替代全局锁，减少竞争）
    _lock: threading.Lock = threading.Lock()

    cls: type[T]
    __wrapped__: type[T]  # 显式声明__wrapped__属性的类型

    def __init__(self, cls: type[T], *args: object, **kwargs: object) -> None:
        """ 初始化包装器，兼容继承场景的可变参数

        Args:
            cls: 要被装饰的类
            *args: 兼容继承时传递的额外参数
            **kwargs: 兼容继承时传递的额外关键字参数
        """
        self.cls = cls
        # self._instances = {}
        self.__wrapped__ = cls

    def __call__(self, *args: object, **kwargs: object) -> T:
        """控制类的实例化过程，确保全局唯一实例（优化锁逻辑）"""
        # 先检查实例是否存在（无锁快速路径），减少锁竞争
        if self.cls in SingletonWrapper._instances:
            return SingletonWrapper._instances[self.cls]

        # 仅在实例不存在时加锁，且锁粒度最小化
        with SingletonWrapper._lock:
            # 双重检查（DCL）：避免多线程下重复创建实例
            if self.cls not in SingletonWrapper._instances:
                SingletonWrapper._instances[self.cls] = self.cls(*args, **kwargs)
        
        return SingletonWrapper._instances[self.cls]

    def __getattr__(self, name: str):
        """
        转发属性访问到原始类，兼容继承场景
        当子类访问父类的属性/方法时，转发到原始类
        """
        return getattr(self.__wrapped__, name)


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
