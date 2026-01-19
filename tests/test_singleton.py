from typing import TypedDict, Unpack

from src.pyutilities.singleton import singleton

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

assert db1 is db2  # 输出: True
assert db1.name == "primary_db"    # 输出: primary_db（保留首次初始化的值）
