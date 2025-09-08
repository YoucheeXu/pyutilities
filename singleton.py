#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import TypeVar, Callable, Generic, overload, cast
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


if __name__ == "__main__":
    from typing import TypedDict, Unpack
    # 示例用法
    class DatabaseConfig(TypedDict):
        """数据库连接的关键字参数类型定义"""
        connection_string: str
        timeout: int
        retry_count: int


    @singleton
    class Database:
        """示例数据库类，使用单例模式确保全局唯一连接"""
        def __init__(self, name: str, /,** config: Unpack[DatabaseConfig]) -> None:
            """
            初始化数据库连接
            位置参数: name - 数据库名称
            关键字参数: 遵循DatabaseConfig类型
            """
            self.name: str = name
            self.config: DatabaseConfig = config
            print(f"初始化数据库 {name}: {config['connection_string']}")

        def query(self, sql: str) -> None:
            print(f"执行查询: {sql}")

    # 首次实例化
    db1 = Database(
        "primary_db",
        connection_string="sqlite:///mydb.db",
        timeout=30,
        retry_count=3
    )
    
    # 再次实例化（应返回同一实例）
    db2 = Database(
        "secondary_db",  # 这个参数会被忽略（单例特性）
        connection_string="postgresql://localhost/db",
        timeout=60,
        retry_count=2
    )
    
    print(db1 is db2)  # 输出: True
    print(db1.name)    # 输出: primary_db（保留首次初始化的值）

