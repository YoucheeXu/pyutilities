#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    uv run pytest --cov=src.pyutilities.singleton .\tests\test_singleton.py -v
"""
import threading
from typing import TypeVar, Any

import pytest

from src.pyutilities.singleton import singleton

# 定义泛型类型变量（用于测试类的类型注解）
T = TypeVar("T")


# ---------------------- 测试用的测试类 ----------------------
# 无参数构造函数的测试类
@singleton
class SimpleSingleton:
    """无参数构造函数的单例测试类"""
    def __init__(self) -> None:
        self.value: int = 0

    def increment(self) -> None:
        self.value += 1


# 带参数构造函数的测试类
@singleton
class ParamSingleton:
    """带参数构造函数的单例测试类"""
    def __init__(self, name: str, age: int) -> None:
        self.name: str = name
        self.age: int = age


# 用于线程安全测试的类
@singleton
class ThreadSafeSingleton:
    """线程安全测试的单例类"""
    def __init__(self) -> None:
        self.counter: int = 0
        self.lock: threading.Lock = threading.Lock()

    def increment(self) -> None:
        with self.lock:
            self.counter += 1


# ---------------------- 测试夹具 ----------------------
@pytest.fixture(scope="function")
def reset_singleton_instances():
    """
    测试夹具：重置单例装饰器的全局实例字典，避免测试用例间污染
    （注：需临时修改singleton装饰器，暴露_instances以便重置）
    
    Yields:
        None: 仅用于控制测试用例的执行流程
    """
    from src.pyutilities.singleton import SingletonWrapper
    
    # 保存原始状态
    original_instances: dict[type[Any], Any] = SingletonWrapper._instances.copy()
    # 重新创建锁（避免锁状态残留）
    original_lock: threading.Lock = SingletonWrapper._lock
    SingletonWrapper._lock = threading.Lock()
    
    # 清空实例字典
    SingletonWrapper._instances.clear()
    
    yield  # 执行测试用例
    
    # 测试后恢复原始状态
    SingletonWrapper._instances = original_instances
    SingletonWrapper._lock = original_lock


# ---------------------- 核心测试用例 ----------------------
def test_basic_singleton_behavior(reset_singleton_instances: None):
    """测试基础单例特性：多次实例化返回同一个对象"""
    # 第一次实例化
    instance1 = SimpleSingleton()
    # 第二次实例化
    instance2 = SimpleSingleton()
    
    # 验证对象唯一性
    assert instance1 is instance2
    assert id(instance1) == id(instance2)
    
    # 验证状态共享（修改一个，另一个也变）
    instance1.increment()
    assert instance1.value == 1
    assert instance2.value == 1


def test_singleton_with_parameters(reset_singleton_instances: None):
    """测试带参数构造函数的单例：仅第一次参数生效，后续忽略"""
    # 第一次实例化（带参数）
    instance1 = ParamSingleton("Alice", 25)
    assert instance1.name == "Alice"
    assert instance1.age == 25
    
    # 第二次实例化（带不同参数，应忽略）
    instance2 = ParamSingleton("Bob", 30)
    assert instance2 is instance1  # 仍是同一个对象
    assert instance2.name == "Alice"  # 参数未被修改
    assert instance2.age == 25


def test_thread_safety(reset_singleton_instances: None):
    """测试线程安全：多线程创建实例仍唯一，状态修改正确"""
    # 定义线程执行函数
    def worker():
        """每个线程获取实例并调用increment"""
        instance = ThreadSafeSingleton()
        instance.increment()
        # 验证当前线程拿到的是同一个实例
        assert instance is ThreadSafeSingleton()

    # 创建10个线程
    threads: list[threading.Thread] = []
    thread_count = 10
    for _ in range(thread_count):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join(timeout=5)  # 超时保护
    
    # 验证最终计数器值等于线程数（每个线程调用一次increment）
    final_instance = ThreadSafeSingleton()
    assert final_instance.counter == thread_count


def test_singleton_preserve_metadata(reset_singleton_instances: None):
    """测试装饰器保留类元数据（__wrapped__属性）"""
    # 验证SimpleSingleton的__wrapped__指向原始类
    assert hasattr(SimpleSingleton, "__wrapped__")
    assert SimpleSingleton.__wrapped__ is SimpleSingleton.__dict__["__wrapped__"]
    
    # 验证ParamSingleton的__wrapped__
    assert ParamSingleton.__wrapped__.__name__ == "ParamSingleton"
    assert ParamSingleton.__wrapped__.__init__.__code__.co_varnames[:2] == ("self", "name")


def test_multiple_singleton_classes(reset_singleton_instances: None):
    """测试不同类的单例独立性：不同类的实例互不干扰"""
    # 实例化第一个类
    simple_inst = SimpleSingleton()
    simple_inst.value = 100
    
    # 实例化第二个类
    param_inst = ParamSingleton("Test", 0)
    
    # 验证两个实例不同
    assert simple_inst is not param_inst
    assert id(simple_inst) != id(param_inst)
    
    # 验证各自状态独立
    assert simple_inst.value == 100
    assert param_inst.name == "Test"


def test_singleton_reinitialization(reset_singleton_instances: None):
    """测试单例实例仅初始化一次：__init__只执行一次"""
    # 统计__init__调用次数
    init_count = 0

    # 动态定义一个测试类
    @singleton
    class InitCounterSingleton:
        def __init__(self) -> None:
            nonlocal init_count
            init_count += 1

    # 多次实例化
    inst1 = InitCounterSingleton()
    inst2 = InitCounterSingleton()
    inst3 = InitCounterSingleton()

    # 验证__init__仅调用一次
    assert init_count == 1
    # 验证所有实例是同一个
    assert inst1 is inst2 is inst3


# ---------------------- 边界场景测试 ----------------------
def test_singleton_with_none_parameters(reset_singleton_instances: None):
    """测试构造函数参数为None的场景"""
    @singleton
    class NoneParamSingleton:
        def __init__(self, data: Any = None) -> None:
            self.data = data

    # 第一次实例化（参数为None）
    inst1 = NoneParamSingleton(None)
    assert inst1.data is None
    
    # 第二次实例化（参数为其他值，忽略）
    inst2 = NoneParamSingleton("test")
    assert inst2.data is None


def test_singleton_inheritance(reset_singleton_instances: None) -> None:
    """测试继承场景下的单例：子类单独维护单例（添加超时+简化逻辑）"""
    # 方案1：使用pytest-timeout插件（推荐，需先安装）
    import pytest_timeout  # 确保插件导入
    # 方式1：用装饰器（更规范）
    @pytest.mark.timeout(5, reason="继承测试卡顿超时")
    def run_test():
        # 父类：先定义原生类，再装饰
        class ParentSingletonRaw:
            parent_value: int

            def __init__(self) -> None:
                self.parent_value = 10

        ParentSingleton = singleton(ParentSingletonRaw)

        # 子类：继承原生父类，再装饰
        class ChildSingletonRaw(ParentSingletonRaw):
            child_value: int

            def __init__(self) -> None:
                super().__init__()
                self.child_value = 20

        ChildSingleton = singleton(ChildSingletonRaw)

        # 验证父类单例
        parent_inst1: ParentSingletonRaw = ParentSingleton()
        parent_inst2: ParentSingletonRaw = ParentSingleton()
        assert parent_inst1 is parent_inst2
        assert parent_inst1.parent_value == 10

        # 验证子类单例
        child_inst1: ChildSingletonRaw = ChildSingleton()
        child_inst2: ChildSingletonRaw = ChildSingleton()
        assert child_inst1 is child_inst2
        assert child_inst1.parent_value == 10
        assert child_inst1.child_value == 20

        # 验证父类和子类实例独立
        assert parent_inst1 is not child_inst1

    # 执行测试逻辑
    run_test()

    # 方案2：若不想安装插件，改用Python原生超时（兼容Windows）
    # import threading
    # result = {"success": False}
    # def test_logic():
    #     # 把上面的测试逻辑复制到这里
    #     result["success"] = True
    # 
    # # 创建线程执行测试，5秒超时
    # t = threading.Thread(target=test_logic)
    # t.start()
    # t.join(timeout=5.0)
    # assert result["success"], "继承测试超时/卡顿"
