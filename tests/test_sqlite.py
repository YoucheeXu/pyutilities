#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    uv run pytest --cov=src.pyutilities.sqlite .\tests\test_sqlite.py -v
    uv run pytest --cov=src.pyutilities.sqlite .\tests\test_sqlite.py --cov-report=html
"""
import sqlite3

import pytest
from pytest import CaptureFixture

from src.pyutilities.sqlite import SQLite

# --------------------------
# Fixtures (Reusable Test Setup)
# --------------------------
@pytest.fixture(scope="function")
def sqlite_instance():
    """Fixture for SQLite instance with persistent in-memory connection."""
    sql = SQLite()
    status, msg = sql.open(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
    assert status == 1, f"Failed to open database: {msg}"

    yield sql  # Provide the instance to test cases

    _ = sql.close()

# --------------------------
# Test Cases
# --------------------------
def test_init_method():
    """Test the __init__ method to verify default attribute values."""
    sql = SQLite()
    assert sql._conn is None

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_open_method():
    """
    Test open() method:
    - First call → creates new connection (no existing conn)
    - Second call → closes existing conn first, then creates new one (covers if self._conn: self._conn.close())
    - Byte path/type parameters work as expected
    """
    sql = SQLite()

    # Scenario 1: First open() → no existing conn (creates new connection)
    status, msg = sql.open(":memory:")
    assert status == 1
    assert sql._conn is not None
    original_conn = sql._conn  # Save reference to original connection

    # Scenario 2: Second open() → triggers if self._conn: self._conn.close()
    status, msg = sql.open("test.db", sqlite3.PARSE_COLNAMES)
    assert status == 1

    # Verify original connection is closed (core coverage for self._conn.close())
    # If original_conn is closed, executing SQL will raise sqlite3.ProgrammingError
    with pytest.raises(sqlite3.ProgrammingError) as excinfo:
        _ = original_conn.execute("SELECT 1")  # Try to use the original connection
    assert "Cannot operate on a closed database" in str(excinfo.value)

    # Verify new connection is created (different from original)
    assert sql._conn is not None
    assert sql._conn != original_conn

    # Scenario 3: Open with byte path (existing conn is closed again)
    status, msg = sql.open(b"test_bytes.db")
    assert status == 1

    # Cleanup
    _ = sql.close()

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_read_version(sqlite_instance: SQLite):
    """Test read_version method: new database should return default user_version (0)."""
    assert sqlite_instance.read_version() == 0

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_write_version(sqlite_instance: SQLite, capsys: CaptureFixture[str]):
    """
    Test write_version method (full coverage of validation logic):
    - Valid integer in range (0 ~ 4294967295)
    - Non-integer type (triggers ValueError)
    - Integer out of lower bound (< 0)
    - Integer out of upper bound (> 4294967295)
    Verify print output and version persistence.
    """
    # Test 1: Valid integer (within range)
    target_version = 123
    sqlite_instance.write_version(target_version)

    # Verify version is persisted across connections
    assert sqlite_instance.read_version() == target_version

    # Verify print output
    captured = capsys.readouterr()
    assert captured.out == f"Successfully set user_version to: {target_version}\n"

    # Test 2: Non-integer type (string) → trigger ValueError
    with pytest.raises(ValueError) as excinfo:
        sqlite_instance.write_version("invalid_version")  # type: ignore
    assert str(excinfo.value) == "user_version must be an integer between 0 and 4294967295 (32-bit unsigned)"

    # Test 3: Non-integer type (float) → trigger ValueError
    with pytest.raises(ValueError) as excinfo:
        sqlite_instance.write_version(123.45)  # type: ignore
    assert str(excinfo.value) == "user_version must be an integer between 0 and 4294967295 (32-bit unsigned)"

    # Test 4: Integer below lower bound (negative) → trigger ValueError
    with pytest.raises(ValueError) as excinfo:
        sqlite_instance.write_version(-5)
    assert str(excinfo.value) == \
        "Invalid user_version: -5. Must be between 0 and 4294967295."

    # Test 5: Integer above upper bound → trigger ValueError
    with pytest.raises(ValueError) as excinfo:
        sqlite_instance.write_version(4294967296)
    assert str(excinfo.value) == \
        "Invalid user_version: 4294967296. Must be between 0 and 4294967295."

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_check_version(sqlite_instance: SQLite):
    """
    Test check_version method (cover all conditional branches):
    - Version within [mini_version, max_version] → return True
    - Version < mini_version → return False
    - Version > max_version → return False
    - Only mini_version provided (max_version uses default) → return True
    """
    # Set baseline version to 50 (persists across connections)
    sqlite_instance.write_version(50)

    # Branch 1: Version in range [10, 100] → True
    assert sqlite_instance.check_version(10, 100) is True

    # Branch 2: Version < mini_version (60) → False
    assert sqlite_instance.check_version(60, 100) is False

    # Branch 3: Version > max_version (40) → False
    assert sqlite_instance.check_version(10, 40) is False

    # Branch 4: Only mini_version provided (max_version = 4294967295) → True
    assert sqlite_instance.check_version(50) is True

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_execute1(sqlite_instance: SQLite):
    """
    Test execute1 method (cover all parameter scenarios):
    - No parameters (create table)
    - Sequence parameters (tuple with ? placeholders)
    - Dictionary parameters (dict with :key placeholders)
    - Empty sequence parameters (equivalent to None)
    """
    # Test 1: No parameters (DDL statement) → table is created and persisted
    assert sqlite_instance.execute1("CREATE TABLE users (id INT, name TEXT)") is True

    # Test 2: Sequence parameters (positional ? placeholders)
    assert sqlite_instance.execute1("INSERT INTO users VALUES (?, ?)", (1, "Alice")) is True

    # Test 3: Dictionary parameters (named :key placeholders)
    assert sqlite_instance.execute1("INSERT INTO users VALUES (:id, :name)", {"id": 2, "name": "Bob"}) is True

    # Test 4: Empty sequence parameters (explicit empty tuple)
    assert sqlite_instance.execute1("DELETE FROM users WHERE id=1", ()) is True

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_get_method(sqlite_instance: SQLite):
    """
    Test get method (cover two scenarios):
    - Query returns data → return first row (tuple)
    - Query returns no data → return None
    """
    # Prepare test table and data (persists across connections)
    _ = sqlite_instance.execute1("CREATE TABLE products (id INT, name TEXT)")
    _ = sqlite_instance.execute1("INSERT INTO products VALUES (1, 'Laptop')")

    # Scenario 1: Data exists → return first row
    result = sqlite_instance.get("SELECT * FROM products WHERE id=1")
    assert result == (1, "Laptop")

    # Scenario 2: No data → return None
    result = sqlite_instance.get("SELECT * FROM products WHERE id=99")
    assert result is None

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_each_method(sqlite_instance: SQLite):
    """
    Test each method (generator functionality):
    - Iterate over generator results (multiple rows)
    - Parameterized query with sequence parameters
    """
    # Prepare test data (persists across connections)
    _ = sqlite_instance.execute1("CREATE TABLE books (id INT, title TEXT)")
    _ = sqlite_instance.execute1("INSERT INTO books VALUES (1, 'Python Basics')")
    _ = sqlite_instance.execute1("INSERT INTO books VALUES (2, 'SQLite Guide')")

    # Test 1: Iterate over generator (all rows)
    generator = sqlite_instance.each("SELECT * FROM books ORDER BY id")
    results = list(generator)  # Convert generator to list for verification
    assert len(results) == 2
    assert results[0] == (1, "Python Basics")
    assert results[1] == (2, "SQLite Guide")

    # Test 2: Parameterized query with sequence parameters
    generator = sqlite_instance.each("SELECT * FROM books WHERE id=?", (2,))
    results = list(generator)
    assert results[0] == (2, "SQLite Guide")

# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_close_method(sqlite_instance: SQLite):
    """Test close method: should always return True."""
    assert sqlite_instance.close() is True


# @pytest.mark.skip(reason="功能未实现，暂不执行")
def test_execute1_edge_case(sqlite_instance: SQLite):
    """
    Edge case test for execute1:
    Verify the conditional check for cursor.execute return value (never False in practice, but cover the branch).
    """
    assert sqlite_instance.execute1("SELECT 1") is True

def test_execute_method(sqlite_instance: SQLite):
    """
    Test execute() method (no auto-commit):
    - No connection → RuntimeError
    - No parameters (CREATE TABLE) → returns True
    - Sequence parameters (? placeholders) → returns True (no commit)
    - Dictionary parameters (:key placeholders) → returns True (no commit)
    - Empty parameters → returns True
    - Invalid SQL → returns False
    """
    # Scenario 1: No connection → RuntimeError
    sql = SQLite()
    with pytest.raises(RuntimeError) as excinfo:
        _ = sql.execute("CREATE TABLE test (id INT)")
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # Scenario 2: No parameters (CREATE TABLE) → returns True
    assert sqlite_instance.execute("CREATE TABLE customers (id INT, name TEXT)") is True

    # Scenario 3: Sequence parameters (? placeholders) → returns True (no commit)
    # Insert data with execute() (no commit yet)
    assert sqlite_instance.execute("INSERT INTO customers VALUES (?, ?)", (1, "Charlie")) is True
    # Verify data is NOT persisted (no commit) → query returns None
    sqlite_instance._conn.rollback()  # Reset connection state
    assert sqlite_instance.get("SELECT * FROM customers WHERE id=1") is None

    # Scenario 4: Dictionary parameters (:key placeholders) → returns True (no commit)
    assert sqlite_instance.execute("INSERT INTO customers VALUES (:id, :name)", {"id": 2, "name": "Diana"}) is True
    sqlite_instance._conn.rollback()  # Reset
    assert sqlite_instance.get("SELECT * FROM customers WHERE id=2") is None

    # Scenario 5: Empty parameters → returns True
    assert sqlite_instance.execute("DELETE FROM customers WHERE id=1", ()) is True

    # Scenario 6: Invalid SQL → raises sqlite3.OperationalError
    with pytest.raises(sqlite3.OperationalError) as excinfo:
        _ = sqlite_instance.execute("INVALID SQL STATEMENT")
    assert "near \"INVALID\": syntax error" in str(excinfo.value)

def test_commit_method(sqlite_instance: SQLite):
    """
    Test commit() method:
    - No connection → AttributeError (conn is None)
    - Commit persists execute() changes
    - Multiple execute() calls + single commit → all changes persist
    """
    # Scenario 1: No connection → AttributeError (conn is None)
    sql = SQLite()
    with pytest.raises(AttributeError) as excinfo:
        sql.commit()
    assert "'NoneType' object has no attribute 'commit'" in str(excinfo.value)

    # Scenario 2: Commit persists execute() changes
    # Step 1: Create table with execute() (no commit)
    _ = sqlite_instance.execute("CREATE TABLE orders (id INT, total FLOAT)")
    # Step 2: Insert data with execute() (no commit)
    _ = sqlite_instance.execute("INSERT INTO orders VALUES (?, ?)", (1, 99.99))
    # Step 3: Verify data is NOT present (no commit)
    sqlite_instance._conn.rollback()  # Reset
    assert sqlite_instance.get("SELECT * FROM orders WHERE id=1") is None

    # Step 4: Re-insert and commit
    _ = sqlite_instance.execute("INSERT INTO orders VALUES (?, ?)", (1, 99.99))
    sqlite_instance.commit()  # Manual commit
    # Step 5: Verify data is persisted
    assert sqlite_instance.get("SELECT * FROM orders WHERE id=1") == (1, 99.99)

    # Scenario 3: Multiple execute() + single commit → all changes persist
    # Insert two rows with execute() (no auto-commit)
    _ = sqlite_instance.execute("INSERT INTO orders VALUES (?, ?)", (2, 199.99))
    _ = sqlite_instance.execute("INSERT INTO orders VALUES (:id, :total)", {"id": 3, "total": 299.99})
    # Commit once
    sqlite_instance.commit()
    # Verify both rows exist
    assert sqlite_instance.get("SELECT * FROM orders WHERE id=2") == (2, 199.99)
    assert sqlite_instance.get("SELECT * FROM orders WHERE id=3") == (3, 299.99)


def test_all_methods_without_connection():
    """
    Test that ALL methods raise RuntimeError when called without open() (covers if not self._conn: ...):
    - read_version()
    - write_version()
    - execute1()
    - get()
    - each()
    - execute() (already covered, but included for completeness)
    """
    # Create SQLite instance WITHOUT calling open() (conn is None)
    sql = SQLite()

    # 1. Test read_version() → RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        _ = sql.read_version()
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # 2. Test write_version() → RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        sql.write_version(100)
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # 3. Test execute1() → RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        _ = sql.execute1("CREATE TABLE test (id INT)")
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # 4. Test get() → RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        _ = sql.get("SELECT 1")
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # 5. Test each() → RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        _ = list(sql.each("SELECT 1"))  # Force generator execution
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # 6. Test execute() (already covered, but verify again for completeness)
    with pytest.raises(RuntimeError) as excinfo:
        _ = sql.execute("CREATE TABLE test (id INT)")
    assert str(excinfo.value) == "Call open() first to initialize connection!"

    # 7. Test commit() → AttributeError (conn is None, no RuntimeError check in commit())
    with pytest.raises(AttributeError) as excinfo:
        sql.commit()
    assert "'NoneType' object has no attribute 'commit'" in str(excinfo.value)
