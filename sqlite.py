#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sqlite3
from collections.abc import Sequence, Mapping
from typing import cast
# from _typeshed import StrOrBytesPath
# from _typeshed import AnyPath
from os import PathLike
""" https://yaoweibin.cn/python-sqlite%e6%97%a5%e6%9c%9f%e6%97%b6%e9%97%b4%e5%a4%84%e7%90%86%e5%85%a8%e6%94%bb%e7%95%a5%e4%bb%8e%e5%85%a5%e9%97%a8%e5%88%b0%e7%b2%be%e9%80%9a/
"""


# 匹配 sqlite3 内部的 _Parameters 类型
SQLParameters = Sequence[object] | Mapping[str, object] | None
StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]

class SQLite:
    """
        def _adapt_datetime(self, dt: datetime.datetime):
            return dt.isoformat()

        def _convert_datetime(self, s):
            return datetime.datetime.fromisoformat(s)

        # 注册适配器和转换器
        sqlite3.register_adapter(datetime.datetime, self._adapt_datetime)
        sqlite3.register_converter("datetime", self._convert_datetime)
    """
    def __init__(self):
        self._conn: sqlite3.Connection
        self._cur: sqlite3.Cursor

    # def open(self, database: StrOrBytesPath, detect_types: int = 0):
    def open(self, database: StrOrBytesPath, detect_types: int = 0):
        """创建与SQLite数据库的连接
        Args:
            database: 数据库标识符，支持：
                - 字符串路径（如 "data.db" 或 "/path/to/db.sqlite"）
                - 字节序列路径（如 b"data.db"，适用于特殊编码路径）
                - 特殊值 ":memory:" 表示内存数据库
                - URI 格式字符串（当 uri=True 时，如 "file:mydb?mode=ro"）
            detect_types: 类型检测标志组合
        """
        self._conn = sqlite3.connect(database, detect_types=detect_types)
        if self._conn:
            self._cur = self._conn.cursor()
        else:
            return -1, f"fail to open {database}"

        return 1, f"{database} is OK to open!"

    # any query: insert/delete/update
    def execute1(self, sql: str, params: SQLParameters = None):
        """ insert/delete/update... with commit
        Args:
            params: 可选参数，用于参数化查询，默认为 None：
                - 序列类型（如 tuple、list）：与 "?" 占位符按位置匹配
                - 字典类型（如 dict）：与 ":key" 占位符按键名匹配
                - None：表示无参数查询
        Example:
            >>> execute("CREATE TABLE users (id INT, name TEXT)")
            >>> execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
            >>> execute("INSERT INTO users VALUES (:id, :name)", {"id": 2, "name": "Bob"})
        """
        ret = self._cur.execute(sql, params if params is not None else ())
        if not ret:
            return False

        self._conn.commit()
        return True

    def execute(self, sql: str, params: SQLParameters = None):
        """ insert/delete/update... without commit
        Args:
            params: 可选参数，用于参数化查询，默认为 None：
                - 序列类型（如 tuple、list）：与 "?" 占位符按位置匹配
                - 字典类型（如 dict）：与 ":key" 占位符按键名匹配
                - None：表示无参数查询
        Example:
            >>> execute("CREATE TABLE users (id INT, name TEXT)")
            >>> execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
            >>> execute("INSERT INTO users VALUES (:id, :name)", {"id": 2, "name": "Bob"})
        """
        _ = self._cur.execute(sql, params if params is not None else ())

    def commit(self):
        self._conn.commit()

    def get(self, query: str):
        """  first row read, 默认游标（返回元组）
        Args:
            query: 查询语句
        Returns:
            当有数据时，返回单行数据（通常是tuple或dict）；
            当无数据时，返回 None。
        """
        _ = self._cur.execute(query)
        record = cast(tuple[object, ...] | None, self._cur.fetchone())
        return record

    def each(self, query: str):
        # set of rows read
        # for row in :
            # yield row
        yield from self._cur.execute(query)

    def close(self) -> bool:
        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.close()
        return True
