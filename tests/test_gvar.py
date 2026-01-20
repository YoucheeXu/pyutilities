#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import pytest
from types import ModuleType

from src.pyutilities import gvar
"""
    uv run pytest --cov=src.pyutilities.gvar .\tests\test_gvar.py -v
"""


@pytest.fixture(scope="function")
def reset_gvar():
    """
    测试夹具：清空非只读全局变量，确保用例独立
    Yields:
        全局变量单例实例
    """
    # 获取全局唯一实例
    gvar_inst = sys.modules["src.pyutilities.gvar"]
    # 清空非只读变量
    gvar_inst.clear_vars()
    # 验证内置只读变量保留
    assert gvar_inst.ver == "0.1.0"
    yield gvar_inst
    # 测试后再次清空
    gvar_inst.clear_vars()


# ---------------------- 核心测试用例 ----------------------
def test_singleton_behavior(reset_gvar: ModuleType) -> None:
    """测试单例特性：多次获取实例是同一个对象"""
    # 方式1：夹具返回的实例
    inst1 = reset_gvar
    # 方式2：从sys.modules获取
    inst2 = sys.modules["src.pyutilities.gvar"]
    # 方式3：直接导入
    from src.pyutilities import gvar as inst3

    # 验证唯一性
    assert inst1 is inst2
    assert inst2 is inst3
    assert id(inst1) == id(inst3)
    # 验证类型一致
    assert isinstance(inst1, type(inst2))


def test_basic_var_operations(reset_gvar: ModuleType) -> None:
    """测试全局变量的基础赋值/获取"""
    gvar_inst = reset_gvar

    # 1. 赋值新变量
    gvar_inst.app_name = "pyutilities"
    gvar_inst.app_mode = "dev"
    gvar_inst.max_workers = 8

    # 2. 验证获取
    assert gvar_inst.app_name == "pyutilities"
    assert gvar_inst.app_mode == "dev"
    assert gvar_inst.max_workers == 8

    # 3. 验证list_vars（仅用户变量）
    assert sorted(gvar_inst.list_vars()) == ["app_mode", "app_name", "max_workers"]

    # 4. 验证list_all_vars（包含内置/只读）
    all_vars = gvar_inst.list_all_vars()
    assert "ver" in all_vars  # 只读变量
    assert "__description__" in all_vars  # 内置属性
    assert "app_name" in all_vars  # 用户变量


def test_read_only_protection(reset_gvar: ModuleType) -> None:
    """测试只读变量保护（ver不可修改/删除）"""
    gvar_inst = reset_gvar

    # 1. 尝试修改只读变量ver（抛异常）
    with pytest.raises(PermissionError) as exc_info:
        gvar_inst.ver = "0.2.0"
    assert "Read-only variable 'ver' cannot be modified" in str(exc_info.value)

    # 2. 尝试删除只读变量ver（抛异常）
    with pytest.raises(PermissionError) as exc_info:
        del gvar_inst.ver
    assert "Read-only variable 'ver' cannot be deleted" in str(exc_info.value)

    # 3. 验证ver仍为原值
    assert gvar_inst.ver == "0.1.0"


def test_safe_get_var(reset_gvar: ModuleType) -> None:
    """测试安全获取变量（get_var方法）"""
    gvar_inst = reset_gvar

    # 1. 设置测试变量
    gvar_inst.db_host = "localhost"

    # 2. 获取存在的变量
    assert gvar_inst.get_var("db_host") == "localhost"
    # 3. 获取不存在的变量（返回None）
    assert gvar_inst.get_var("db_port") is None
    # 4. 获取不存在的变量（指定默认值）
    assert gvar_inst.get_var("db_port", 3306) == 3306


def test_clear_vars(reset_gvar: ModuleType) -> None:
    """测试清空非只读变量"""
    gvar_inst = reset_gvar

    # 1. 设置多个测试变量
    gvar_inst.var1 = 100
    gvar_inst.var2 = "test"
    gvar_inst.var3 = [1, 2, 3]
    assert gvar_inst.list_vars() == ["var1", "var2", "var3"]

    # 2. 清空变量
    gvar_inst.clear_vars()

    # 3. 验证清空结果
    assert gvar_inst.list_vars() == []
    # 4. 验证只读变量仍存在
    assert gvar_inst.ver == "0.1.0"
    # 5. 验证内置属性仍存在
    assert gvar_inst.__description__ == "Singleton-based global variable manager"


def test_var_deletion(reset_gvar: ModuleType) -> None:
    """测试删除普通全局变量"""
    gvar_inst = reset_gvar

    # 1. 设置测试变量
    gvar_inst.test_var = "delete_me"
    assert gvar_inst.test_var == "delete_me"

    # 2. 删除变量
    del gvar_inst.test_var

    # 3. 验证删除成功
    assert "test_var" not in gvar_inst.list_vars()
    assert gvar_inst.get_var("test_var") is None

    # 4. 尝试删除不存在的变量（抛异常）
    with pytest.raises(NameError) as exc_info:
        del gvar_inst.non_exist_var
    assert "Global variable 'non_exist_var' does not exist" in str(exc_info.value)


def test_cross_module_share(reset_gvar: ModuleType) -> None:
    """测试跨模块共享变量（模拟不同模块导入）"""
    # 1. 模块1导入并设置变量
    import src.pyutilities.gvar as gvar1
    gvar1.shared_var = "cross_module"

    # 2. 模块2导入并获取变量
    import src.pyutilities.gvar as gvar2
    assert gvar2.shared_var == "cross_module"

    # 3. 验证是同一个实例
    assert gvar1 is gvar2
    assert gvar1.shared_var == gvar2.shared_var
