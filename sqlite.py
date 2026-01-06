#!/usr/bin/python3
# -*- coding: utf-8 -*-
from os import PathLike
import sqlite3
from collections.abc import Sequence, Mapping
from typing import cast
from collections.abc import Generator
# from _typeshed import StrOrBytesPath
# from _typeshed import AnyPath
""" Python SQLite日期时间处理全攻略:从入门到精通
https://yaoweibin.cn/python-sqlite%e6%97%a5%e6%9c%9f%e6%97%b6%e9%97%b4%e5%a4%84%e7%90%86%e5%85%a8%e6%94%bb%e7%95%a5%e4%bb%8e%e5%85%a5%e9%97%a8%e5%88%b0%e7%b2%be%e9%80%9a/
"""


# Match the internal `_Parameters` type of sqlite3
SQLParameters = Sequence[object] | Mapping[str, object] | None
StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]

class SQLite:
    """
        def _adapt_datetime(self, dt: datetime.datetime):
            return dt.isoformat()

        def _convert_datetime(self, s):
            return datetime.datetime.fromisoformat(s)

        # register adapters and converters
        sqlite3.register_adapter(datetime.datetime, self._adapt_datetime)
        sqlite3.register_converter("datetime", self._convert_datetime)
    """
    def __init__(self):
        self._conn: sqlite3.Connection
        self._cur: sqlite3.Cursor

    def open(self, database: StrOrBytesPath, detect_types: int = 0):
        """Creates a connection to an SQLite database.

        Args:
            database: Database identifier, which supports:
                - String path (e.g., "data.db" or "/path/to/db.sqlite")
                - Byte sequence path (e.g., b"data.db", suitable for paths with special encodings)
                - Special value ":memory:" indicating an in-memory database
                - URI-formatted string (when uri=True, e.g., "file:mydb?mode=ro")
            detect_types: Combination of type detection flags
        """
        self._conn = sqlite3.connect(database, detect_types=detect_types)
        if self._conn:
            self._cur = self._conn.cursor()
        else:
            return -1, f"fail to open {database}"

        return 1, f"{database} is OK to open!"

    def read_version(self):
        """ reads the user_version metadata of an SQLite database.

        Return:
            int: 32bits unsinged integer value of user_version (default is 0 for new databases)
        """
        cursor = self._conn.execute("PRAGMA user_version;")
        version = cast(int, cursor.fetchone()[0])
        return version

    def write_version(self, target_version: int):
        """ writes a new value to the user_version metadata of an SQLite database.

        Args:
            target_version: Target version number (must be a 32-bit unsigned integer in range 0 ~ 4294967295).

        Raises:
            ValueError: If target_version is out of the valid range or not an integer.
        """
        # not isinstance(target_version, int)
        if target_version < 0 or target_version > 4294967295:
            raise ValueError("user_version must be an integer between 0 and 4294967295")

        # with sqlite3.connect(db_path) as conn:
        _ = self._conn.execute(f"PRAGMA user_version = {target_version};")
        print(f"Successfully set user_version to: {target_version}")

    def check_version(self, mini_version: int, max_version: int = 4294967295):
        version = self.read_version()
        if mini_version <= version <= max_version:
            return True
        else:
            return False

    def execute1(self, sql: str, params: SQLParameters = None):
        """ insert/delete/update... with commit

        Args:
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters
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
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Example:
            >>> execute("CREATE TABLE users (id INT, name TEXT)")
            >>> execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
            >>> execute("INSERT INTO users VALUES (:id, :name)", {"id": 2, "name": "Bob"})
        """
        _ = self._cur.execute(sql, params if params is not None else ())

    def commit(self):
        self._conn.commit()

    def get(self, query: str):
        """read the first row of query results (default cursor returns a tuple).

        Args:
            query: the query statement.

        Returns:
            returns a single row of data (usually a tuple or dictionary) when data exists;
                returns None when no data is available.
        """
        _ = self._cur.execute(query)
        record = cast(tuple[object, ...] | None, self._cur.fetchone())
        return record

    def each(self, query: str, params: SQLParameters = None) -> Generator[object, object, object]:
        """ each 

        Args:
            query: the query statement       
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Returns:
            return Generator
        """
        yield from self._cur.execute(query, params if params is not None else ())

    def close(self) -> bool:
        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.close()
        return True


if __name__ == "__main__":
    DB_PATH = "test.db"

    sqlite = SQLite()
    _ = sqlite.open(DB_PATH)

    # 1. Read initial version (default is 0)
    initial_version = sqlite.read_version()
    print(f"Initial user_version: {initial_version}")

    # 2. Write a new version (e.g., 100)
    sqlite.write_version(100)

    # 3. Verify the updated version
    updated_version = sqlite.read_version()
    print(f"Updated user_version: {updated_version}")

    # 4. check version: require version exactly match
    ret = sqlite.check_version(100, 100)
    print(f"user_version exactly match: {ret}")

    # 5. check version: require version satisfy mini version
    ret = sqlite.check_version(99)
    print(f"user_version satisfy mini version: {ret}")

    # 6. check version: require version not exceed max version
    ret = sqlite.check_version(0, 99)
    print(f"user_version not exceed max version 99: {ret}")

    # 7. check version: require version not exceed max version
    ret = sqlite.check_version(0, 101)
    print(f"user_version not exceed max version 101: {ret}")
