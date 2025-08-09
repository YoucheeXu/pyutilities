#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sqlite3
# from typing import Literal, Any
# from _typeshed import AnyPath
""" https://yaoweibin.cn/python-sqlite%e6%97%a5%e6%9c%9f%e6%97%b6%e9%97%b4%e5%a4%84%e7%90%86%e5%85%a8%e6%94%bb%e7%95%a5%e4%bb%8e%e5%85%a5%e9%97%a8%e5%88%b0%e7%b2%be%e9%80%9a/
"""


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
        self.__conn: sqlite3.Connection
        self.__cur: sqlite3.Cursor

    # def open(self, database: StrOrBytesPath, detect_types: int = 0):
    def open(self, database, detect_types: int = 0):
        self.__conn = sqlite3.connect(database, detect_types=detect_types)
        if self.__conn:
            self.__cur = self.__conn.cursor()
        else:
            return -1, f"fail to open {database}"

        return 1, f"{database} is OK to open!"

    # any query: insert/delete/update
    def execute1(self, sql: str, parameters = ()):
        """ insert/delete/update... with commit
        """
        ret = self.__cur.execute(sql, parameters)
        if not ret:
            return False

        self.__conn.commit()
        return True

    def execute(self, sql: str, parameters = ()):
        """ insert/delete/update... without commit
        """
        _ = self.__cur.execute(sql, parameters)

    def commit(self):
        self.__conn.commit()

    def get(self, query: str):
        """  first row read
        """
        _ = self.__cur.execute(query)
        records = self.__cur.fetchone()
        return records[0]

    def each(self, query: str):
        # set of rows read
        # for row in :
            # yield row
        yield from self.__cur.execute(query)

    def close(self) -> bool:
        if self.__cur:
            self.__cur.close()
        if self.__conn:
            self.__conn.close()
        return True
