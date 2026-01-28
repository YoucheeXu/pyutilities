#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    uv run pytest --cov=src.pyutilities.const .\tests\test_const.py -v
"""
import sys
from types import ModuleType

import pytest

from src.pyutilities.singleton import singleton
from src.pyutilities import const



# ---------------------- 测试前置/后置处理 ----------------------
@pytest.fixture(scope="function")
def reset_const_module():
    """
    测试夹具：彻底清空用户常量，返回全局唯一的const模块实例
    """
    # 从sys.modules获取全局唯一实例（避免__import__重新加载）
    const_mod = sys.modules["src.pyutilities.const"]
    # 强制清空所有用户常量
    const_mod.clear_user_constants()
    # 验证清空结果（确保列表为空）
    assert const_mod.list_constants() == []
    yield const_mod
    # 测试后再次清空
    const_mod.clear_user_constants()


# ---------------------- 核心功能测试 ----------------------

def test_singleton_behavior(reset_const_module: ModuleType):
    """测试单例特性：多次获取模块实例是同一个对象"""
    # 方式1：夹具返回的实例
    const_mod1 = reset_const_module
    # 方式2：从sys.modules获取（模拟其他模块导入）
    # const_mod2 = __import__("src.pyutilities.const").pyutilities.const
    const_mod2 = sys.modules["src.pyutilities.const"]

    # 核心验证：ID相同+对象相同
    assert id(const_mod1) == id(const_mod2)
    assert const_mod1 is const_mod2
     # 额外验证：都是_const类的实例
    assert isinstance(const_mod1, type(const_mod2))


def test_const_naming_constraint(reset_const_module: ModuleType):
    """测试常量命名约束：非全大写名称抛出 ConstCaseError"""
    const_mod = reset_const_module

    # 测试1：小写名称（触发异常）
    with pytest.raises(const_mod.ConstCaseError) as exc_info:
        const_mod.min_value = 1  # 小写名称，触发约束
    assert "must be in uppercase" in str(exc_info.value)

    # 测试2：混合大小写（触发异常）
    with pytest.raises(const_mod.ConstCaseError):
        const_mod.MaxRetry = 5

    # 测试3：全大写（正常赋值）
    const_mod.MAX_RETRY = 10
    assert const_mod.MAX_RETRY == 10


def test_const_immutable(reset_const_module: ModuleType):
    """测试常量不可修改：重复赋值抛ConstError"""
    const_mod = reset_const_module

    # 先定义一个合法常量
    const_mod.TIMEOUT = 30
    assert const_mod.TIMEOUT == 30

    # 尝试修改常量，抛出 ConstError
    with pytest.raises(const_mod.ConstError) as exc_info:
        const_mod.TIMEOUT = 60
    assert "Cannot modify constant 'TIMEOUT'" in str(exc_info.value)

    # 验证常量值未被修改
    assert const_mod.TIMEOUT == 30


def test_const_undeletable(reset_const_module: ModuleType):
    """测试常量不可删除：删除常量抛出 ConstError"""
    const_mod = reset_const_module

    # 先定义常量
    const_mod.MAX_CONN = 100
    assert const_mod.MAX_CONN == 100

    # 删除已定义常量（触发异常）
    with pytest.raises(const_mod.ConstError) as exc_info:
        del const_mod.MAX_CONN
    assert "Cannot delete constant 'MAX_CONN'" in str(exc_info.value)

    # 删除不存在的常量（抛NameError）
    with pytest.raises(NameError) as exc_info:
        del const_mod.NOT_EXIST_CONST
    assert "Constant 'NOT_EXIST_CONST' is not defined" in str(exc_info.value)


def test_list_constants_function(reset_const_module: ModuleType):
    """测试list_constants：正确列出用户常量"""
    const_mod = reset_const_module

    # 定义多个常量
    const_mod.MAX_RETRY = 5
    const_mod.TIMEOUT = 30
    const_mod.DB_URL = "mysql://localhost:3306/test"

    # 验证列表内容
    constants = const_mod.list_constants()
    assert sorted(constants) == ["DB_URL", "MAX_RETRY", "TIMEOUT"]

    # 验证内置属性（如__version__）不会被列出
    assert "__version__" not in constants
    assert "__description__" not in constants


def test_get_constant_function(reset_const_module: ModuleType):
    """测试get_constant：存在返回值，不存在返回None"""
    const_mod = reset_const_module

    # 定义常量
    const_mod.MAX_RETRY = 5

    # 测试1：获取存在的常量
    assert const_mod.get_constant("MAX_RETRY") == 5

    # 测试2：获取不存在的常量，返回None（不抛异常）
    assert const_mod.get_constant("NOT_EXIST") is None


def test_builtin_attributes(reset_const_module: ModuleType):
    """测试内置属性保留：清空后仍存在"""
    const_mod = reset_const_module

    # 验证内置属性存在且值正确
    assert const_mod.__version__ == "1.0.0"
    assert const_mod.__description__ == "A singleton-based constant management module"
    assert hasattr(const_mod, "__file__")
    assert const_mod.__name__ == "src.pyutilities.const"

    # 清空后验证内置属性仍存在
    const_mod.clear_user_constants()
    assert const_mod.__version__ == "1.0.0"


def test_getattr_error_message(reset_const_module: ModuleType):
    """测试获取不存在常量：抛NameError"""
    const_mod = reset_const_module

    # 访问不存在的常量，抛出 NameError 且提示正确
    with pytest.raises(NameError) as exc_info:
        _ = const_mod.NOT_EXIST_CONST
    assert "Constant 'NOT_EXIST_CONST' is not defined" in str(exc_info.value)


# ---------------------- 边界场景测试 ----------------------
def test_empty_const_list(reset_const_module: ModuleType):
    """测试无用户常量时 list_constants 返回空列表"""
    const_mod = reset_const_module

    # 夹具已清空，直接验证
    assert const_mod.list_constants() == []

    # 定义常量后清空，再次验证
    const_mod.TEST_CONST = 123
    assert const_mod.list_constants() == ["TEST_CONST"]
    const_mod.clear_user_constants()
    assert const_mod.list_constants() == []


def test_const_with_underscore(reset_const_module: ModuleType):
    """测试包含下划线的全大写常量（合法场景）"""
    const_mod = reset_const_module

    # 定义包含下划线的常量
    const_mod.USER_NAME = "admin"
    const_mod.DB_PORT = 3306

    # 验证常量可正常访问
    assert const_mod.USER_NAME == "admin"
    assert const_mod.DB_PORT == 3306

    # 验证列表包含这些常量
    assert "USER_NAME" in const_mod.list_constants()
    assert "DB_PORT" in const_mod.list_constants()
