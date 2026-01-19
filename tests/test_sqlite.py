import os
# import sys
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(root_path)

from src.pyutilities.sqlite import SQLite
"""
    uv run pytest --cov=src.pyutilities.sqlite .\tests\test_sqlite.py -v
"""


def test_sqlite():
    DB_PATH = "test.db"

    if os.path.isfile(DB_PATH):
            os.remove(DB_PATH)

    sqlite = SQLite()
    _ = sqlite.open(DB_PATH)

    # 1. Read initial version (default is 0)
    initial_version = sqlite.read_version()
    assert initial_version == 0
    print(f"Initial user_version: {initial_version}")

    # 2. Write a new version (e.g., 100)
    sqlite.write_version(100)

    # 3. Verify the updated version
    updated_version = sqlite.read_version()
    assert updated_version == 100
    print(f"Updated user_version: {updated_version}")

    # 4. check version: require version exactly match
    ret = sqlite.check_version(100, 100)
    assert ret
    print(f"user_version exactly match: {ret}")

    # 5. check version: require version satisfy mini version
    ret = sqlite.check_version(99)
    assert ret
    print(f"user_version satisfy mini version: {ret}")

    # 6. check version: require version not exceed max version
    ret = sqlite.check_version(0, 99)
    assert not ret
    print(f"user_version not exceed max version 99: {ret}")

    # 7. check version: require version not exceed max version
    ret = sqlite.check_version(0, 101)
    assert ret
    print(f"user_version not exceed max version 101: {ret}")

    _ = sqlite.close()
