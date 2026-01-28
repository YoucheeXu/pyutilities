#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
A simplified, persistent-connection wrapper for SQLite database operations.

This module provides a user-friendly interface for common SQLite tasks:
- Persistent database connections (avoids repeated connection setup/teardown)
- SQLite database version metadata management (user_version PRAGMA)
- Parameterized SQL queries (supports ?/:key placeholders)
- Auto-commit and manual-commit execution modes
- Generator-based result iteration
- Safe connection cleanup and resource management

Key Features:
- Idempotent connection handling (safe to call open() multiple times)
- Explicit error checking for uninitialized connections
- Consistent parameterized query interface
- Clean resource management (cursor/connection closure)
"""
from os import PathLike
import sqlite3
from collections.abc import Sequence, Mapping
from typing import cast
from collections.abc import Generator

# Type aliases for SQLite parameterized queries and database paths
# Sequence/dict for parameterized queries (None = no parameters)
SQLParameters = Sequence[object] | Mapping[str, object] | None
# Supported SQLite database path types (string/bytes/PathLike)
StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]


class SQLite:
    """ A simplified wrapper class for SQLite database operations with persistent connections.

    This class manages a single persistent SQLite connection (reused across all method calls)
    to avoid the overhead of repeated connection creation/teardown, and provides intuitive
    methods for common database tasks like version management, query execution, and result retrieval.

    Attributes:
        _conn (sqlite3.Connection | None): Persistent SQLite database connection object.
            None if no connection has been opened or if close() has been called.
    """
    def __init__(self):
        """ Initialize an empty SQLite instance with no active connection."""
        self._conn: sqlite3.Connection | None = None

    def open(self, database: StrOrBytesPath, detect_types: int = 0):
        """ Establish or re-establish a persistent connection to an SQLite database.

        Closes any existing connection before creating a new one (idempotent operation),
        ensuring only one active connection exists at a time.

        Args:
            database: Database identifier, which supports:
                - String path (e.g., "data.db" or "/path/to/db.sqlite")
                - Byte sequence path (e.g., b"data.db", suitable for paths with special encodings)
                - Special value ":memory:" indicating an in-memory database
                - URI-formatted string (when uri=True, e.g., "file:mydb?mode=ro")
            detect_types: Bitmask of SQLite type detection flags (e.g., sqlite3.PARSE_DECLTYPES,
                sqlite3.PARSE_COLNAMES) to enable automatic type conversion between SQLite and Python.

        Returns:
            tuple[int, str]: Status code (1 = success) and human-readable success message.

        Example:
            >>> db = SQLite()
            >>> status, msg = db.open(":memory:", sqlite3.PARSE_DECLTYPES)
            >>> print(status, msg)
            1 OK to open :memory:!
        """
        # Close existing connection if open (idempotent)
        if self._conn:
            self._conn.close()

        # Create new persistent connection (reused for all subsequent operations)
        self._conn = sqlite3.connect(database, detect_types=detect_types)

        return 1, f"OK to open {database}!"

    def read_version(self):
        """ Retrieve the user_version metadata value from the SQLite database.

        The user_version is a 32-bit unsigned integer stored in the SQLite database header
        (default = 0 for new databases) used for application-level version tracking.

        Return:
            int: 32-bit unsigned integer value of the database's user_version PRAGMA
                (default is 0 for new databases)

        Raises:
            RuntimeError: If called before open() (no active database connection).

        Example:
            >>> db.open(":memory:")
            >>> print(db.read_version())
            0
        """
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        # Execute PRAGMA to get user_version (single-row, single-column result)
        cursor = self._conn.execute("PRAGMA user_version;")
        version = cast(int, cursor.fetchone()[0])
        cursor.close()  # Clean up cursor to prevent resource leaks
        return version

    def write_version(self, target_version: int):
        """ Set the user_version metadata value for the SQLite database.

        The target version must be a 32-bit unsigned integer (0 to 4294967295). This value
        is persisted to the database header and survives database restarts.

        Args:
            target_version: Target version number (must be a 32-bit unsigned integer in range 0 ~ 4294967295).

        Raises:
            RuntimeError: If called before open() (no active database connection).
            ValueError: If target_version is not an integer, negative, or exceeds 4294967295.

        Side Effects:
            Prints a confirmation message to stdout with the new version value.
            Commits the PRAGMA change immediately to ensure persistence.

        Example:
            >>> db.open(":memory:")
            >>> db.write_version(10)
            Successfully set user_version to: 10
            >>> print(db.read_version())
            10
        """
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        # Validate version type and range (32-bit unsigned integer constraints)
        if not isinstance(target_version, int):
            raise ValueError(
                "user_version must be an integer between 0 and 4294967295 (32-bit unsigned)"
            )
        if target_version < 0 or target_version > 4294967295:
            raise ValueError(
                f"Invalid user_version: {target_version}. Must be between 0 and 4294967295."
            )

        # Execute PRAGMA to set version and commit immediately
        cursor = self._conn.execute(f"PRAGMA user_version = {target_version};")
        self._conn.commit()  # PRAGMA changes require explicit commit for persistence
        cursor.close()
        print(f"Successfully set user_version to: {target_version}")

    def check_version(self, mini_version: int, max_version: int = 4294967295):
        """ Validate if the database's user_version falls within a specified range.

        Convenience method to check version compatibility (e.g., for schema migrations).
        Uses the maximum 32-bit unsigned integer (4294967295) as the default upper bound.

        Args:
            min_version: Minimum acceptable user_version (inclusive).
            max_version: Maximum acceptable user_version (inclusive), default = 4294967295.

        Returns:
            bool: True if current user_version is between min_version and max_version (inclusive),
                False otherwise.

        Raises:
            RuntimeError: If called before open() (propagated from read_version()).

        Example:
            >>> db.open(":memory:")
            >>> db.write_version(5)
            >>> db.check_version(1, 10)  # True
            >>> db.check_version(6, 10)  # False
        """
        version = self.read_version()
        return mini_version <= version <= max_version

    def execute1(self, sql: str, params: SQLParameters = None):
        """ Execute SQL with **automatic commit** (for write operations: INSERT/UPDATE/DELETE/CREATE).

        Ideal for single, atomic write operations that need immediate persistence. Supports
        parameterized queries to prevent SQL injection.

        Args:
            sql: Valid SQLite SQL statement (DDL/DML).
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Returns:
            bool: True if the SQL execution succeeds, False if it fails (e.g., invalid syntax).

        Raises:
            RuntimeError: If called before open() (no active database connection).
            sqlite3.Error: For SQL execution errors (e.g., syntax error, constraint violation)
                (no exception handling in this method).

        Example:
            >>> db.open(":memory:")
            >>> db.execute1("CREATE TABLE users (id INT, name TEXT)")  # True
            >>> db.execute1("INSERT INTO users VALUES (?, ?)", (1, "Alice"))  # True
            >>> db.execute1("INSERT INTO users VALUES (:id, :name)", {"id": 2, "name": "Bob"})  # True
        """
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        # Create cursor, execute query, commit immediately
        cursor = self._conn.cursor()
        ret = cursor.execute(sql, params if params is not None else ())
        self._conn.commit()  # Auto-commit for immediate persistence
        cursor.close()
        return bool(ret)

    def execute(self, sql: str, params: SQLParameters = None):
        """ Execute SQL without **automatic commit** (for write operations: INSERT/UPDATE/DELETE/CREATE).
        Ideal for multiple related write operations that should be committed together
        (call commit() manually to persist changes). Supports parameterized queries.

        Args:
            sql: Valid SQLite SQL statement (DDL/DML).
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Returns:
            bool: True if the SQL execution succeeds, False if it fails (e.g., invalid syntax).

        Raises:
            RuntimeError: If called before open() (no active database connection).
            sqlite3.Error: For SQL execution errors (e.g., syntax error, constraint violation)
                (no exception handling in this method).

        Examples:
            >>> db.open(":memory:")
            >>> db.execute("CREATE TABLE orders (id INT, total FLOAT)")  # True
            >>> db.execute("INSERT INTO orders VALUES (?, ?)", (1, 99.99))  # True
            >>> db.execute("INSERT INTO orders VALUES (:id, :total)", {"id": 2, "total": 199.99})  # True
            >>> db.commit()  # Persist all changes
        """
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

         # Create cursor, execute query (no commit)
        cursor = self._conn.cursor()
        execution_result = cursor.execute(sql, params if params is not None else ())
        cursor.close()

        # Return True if execution succeeded (cursor object is truthy)
        return bool(execution_result)

    def commit(self):
        """ Manually commit all pending changes from execute() calls to the database.

        Required to persist changes made with the execute() method (no auto-commit).
        Safe to call multiple times (idempotent if no pending changes).

        Raises:
            AttributeError: If called before open() (self._conn is None).
            sqlite3.Error: If commit fails (e.g., database locked, write error).

        Example:
            >>> db.open(":memory:")
            >>> db.execute("INSERT INTO users VALUES (1, 'Alice')")
            >>> db.commit()  # Persist the insert
        """
        self._conn.commit()

    def get(self, query: str):
        """ Retrieve the **first row** of a SELECT query result (as a tuple).

        Useful for queries expected to return a single row (e.g., SELECT with PRIMARY KEY).
        Returns None if the query returns no results.

        Args:
            query: Valid SQLite SELECT statement (parameterized queries not supported here).

        Returns:
            Optional[tuple[object, ...]]: First row of results as a tuple if data exists,
                None if no rows are returned.

        Raises:
            RuntimeError: If called before open() (no active database connection).
            sqlite3.Error: For invalid query syntax or execution errors.

        Examples:
            >>> db.open(":memory:")
            >>> db.execute1("INSERT INTO users VALUES (1, 'Alice')")
            >>> db.get("SELECT * FROM users WHERE id=1")  # (1, 'Alice')
            >>> db.get("SELECT * FROM users WHERE id=99")  # None
        """
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        # Create cursor, execute query, fetch first row
        cursor = self._conn.cursor()
        cursor.execute(query)
        result = cast(tuple[object, ...] | None, cursor.fetchone())
        cursor.close()

        return result

    def each(self, query: str, params: SQLParameters = None) -> Generator[object, object, object]:
        """ Return a generator to iterate over **all rows** of a query result (lazy evaluation).

        Efficient for large result sets (does not load all rows into memory at once).
        Each iteration returns a row as a tuple.

        Args:
            query: the query statement
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Yields:
            tuple[object, ...]: Each row of the query result as a tuple.

        Raises:
            RuntimeError: If called before open() (no active database connection).
            sqlite3.Error: For invalid query syntax or execution errors.

        Example:
            >>> db.open(":memory:")
            >>> db.execute1("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
            >>> for row in db.each("SELECT * FROM users ORDER BY id"):
            ...     print(row)
            (1, 'Alice')
            (2, 'Bob')
        """
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        # Create cursor, execute query, yield rows one at a time
        cursor = self._conn.cursor()
        yield from cursor.execute(query, params if params is not None else ())
        cursor.close()  # Clean up cursor after generator is exhausted

    def close(self) -> bool:
        """ Safely close the persistent database connection and clean up resources.

        Idempotent operation (safe to call multiple times even if no connection exists).
        Clears the connection reference to prevent accidental use of a closed connection.

        Returns:
            bool: Always returns True (for consistency/idempotency).

        Side Effects:
            Closes the underlying sqlite3.Connection if open.
            Sets self._conn to None to mark the connection as closed.

        Example:
            >>> db.open(":memory:")
            >>> db.close()  # True
            >>> db._conn  # None
        """
        if self._conn:
            self._conn.close()
            self._conn = None  # Clear reference to prevent use of closed connection
        return True
