#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Pytest test suite for logit.py
# Run full test suite with coverage
uv run pytest --cov=src.pyutilities.logit .\tests\test_logit.py -v
uv run pytest --cov=src.pyutilities.logit --cov-report=html tests/test_logit.py

# Run only EmailLogit tests (focus on your modifications)
uv run pytest --cov=src.pyutilities.logit .\tests\test_logit.py -v -k "email_logit"
"""
import time
import inspect
import types
import smtplib

from unittest.mock import (
    Mock,
    MagicMock,
    patch
)
from pathlib import Path
from typing import (
    TypeVar
)

import pytest
from pytest import (
    CaptureFixture,
    MonkeyPatch
)

# Import the module
from src.pyutilities.logit import (
    _get_caller_location,
    _resolve_index,
    po, pv, pe, time_calc,
    LogLevel, Logit, EmailLogit,
)


# Type Variables for Generic Annotations
T = TypeVar("T")
P = TypeVar("P")  # For function parameters
R = TypeVar("R")  # For function return values


# --------------------------
# Test Fixtures
# --------------------------
@pytest.fixture
def mock_frameinfo():
    """Fixture: Mock inspect.getframeinfo 返回有效 FrameInfo 对象"""
    # 构造标准的 FrameInfo 对象（无需mock frame/code）
    mock_frame_info = inspect.FrameInfo(
        frame=None,
        filename="/test/file.py",
        lineno=42,
        function="test_func",
        code_context=["test_code_line"],
        index=0
    )
    with patch("inspect.getframeinfo", return_value=mock_frame_info):
        yield mock_frame_info

@pytest.fixture
def mock_no_frame():
    """Fixture: Mock currentframe 返回 None"""
    with patch("inspect.currentframe", return_value=None):
        yield

@pytest.fixture
def mock_caller_frame_none():
    """Fixture: Mock caller_frame 为 None"""
    mock_current_frame = Mock(spec=types.FrameType)
    mock_current_frame.f_back = None
    with patch("inspect.currentframe", return_value=mock_current_frame):
        yield

def create_mock_frameinfo(
    filename: str = "/test/file.py",
    lineno: int = 42,
    function: str = "test_func",
    code_context: list[str] | None = None,
    index: int = 0
) -> inspect.FrameInfo:
    if code_context is None:
        code_context = [f"test_code_line"]
    return inspect.FrameInfo(
        frame=None,  # 无需实际 frame
        filename=filename,
        lineno=lineno,
        function=function,
        code_context=code_context,
        index=index
    )

def test_get_caller_location_valid_frame(mock_frameinfo):
    """Test: Valid current/caller frame"""
    location = _get_caller_location()
    assert location == (42, '/test/file.py')

def test_get_caller_location_current_frame_none():
    """Test: current_frame = None"""
    # Simulate inspect.currentframe() returning None (edge case)
    with patch("inspect.currentframe", return_value=None):
        location = _get_caller_location()
        assert location == ('unknown', 'unknown')

def test_get_caller_location_caller_frame_none():
    """Test: current_frame exists but caller_frame = None"""
    # Mock current frame with no back frame (edge case)
    mock_current_frame = Mock(spec=types.FrameType)
    mock_current_frame.f_back = None
    mock_current_frame.f_lasti = 0
    
    with patch("inspect.currentframe", return_value=mock_current_frame):
        location = _get_caller_location()
        assert location == ('unknown', 'unknown')

# def test_get_caller_location_missing_filename(mock_frameinfo_no_filename):
def test_get_caller_location_missing_filename():
    """Test: Valid frame but missing co_filename"""
    mock_frameinfo_no_filename = create_mock_frameinfo(
        filename=None, # missing file name
        lineno=42,
        function="test_func",
        code_context=["test_code_line"],
        index=0
    )
    # mock_frameinfo_no_filename.
    with patch("inspect.getframeinfo", return_value=mock_frameinfo_no_filename):
        location = _get_caller_location()
        assert location == (42, None)

def test_get_caller_location_missing_lineno():
    """Test: Valid frame but missing lineno"""
    mock_frameinfo = create_mock_frameinfo(
        filename="/test/file.py",
        lineno=None,
        function="test_func",
        code_context=["test_code_line"],
        index=0
    )
    with patch("inspect.getframeinfo", return_value=mock_frameinfo):
        location = _get_caller_location()
        assert location == (None, '/test/file.py')

def test_get_caller_location_memory_cleanup(mock_frameinfo):
    """Test: del statements execute (memory cleanup path)"""
    _get_caller_location()
    assert True

# --------------------------
# Test _resolve_index
# --------------------------
def test_resolve_index_basic():
    """Test basic index resolution (variable references)"""
    locals_dict = {
        "i": 5,
        "j": 10,
        "none_val": None,
        "empty_str": "",
        "space_only": "  ",
        "mixed": "  test  "
    }

    # Test direct variable reference
    assert _resolve_index("i", locals_dict) == '5'
    assert _resolve_index("j", locals_dict) == '10'

    # Test special values
    assert _resolve_index("none_val", locals_dict) == 'None'
    assert _resolve_index("empty_str", locals_dict) == "<EMPTY>"
    assert _resolve_index("space_only", locals_dict) == "<SPACE:2>"
    assert _resolve_index("mixed", locals_dict) == "'  test  '"

    # Test complex expressions
    assert _resolve_index("i + j", locals_dict) == '15'
    assert _resolve_index("i * 2 - 3", locals_dict) == '7'

    # Test invalid expressions (return original)
    assert _resolve_index("undefined_var", locals_dict) == "undefined_var"
    assert _resolve_index("i + 'string'", locals_dict) == "i + 'string'"  # TypeError
    assert _resolve_index(")", locals_dict) == ")"  # SyntaxError

def test_resolve_index_edge_cases():
    """Test _resolve_index for edge cases"""
    locals_dict = {
        "zero_val": 0,
        "bool_val": False,
        "bytes_val": b"test",
        "dict_val": {"key": "val"},
        "list_val": [1,2,3],
        "empty_list": [],
        "multi_space": "   ",  # 3 spaces
    }

    # Test numeric zero
    assert _resolve_index("zero_val", locals_dict) == '0'
    # Test boolean False
    assert _resolve_index("bool_val", locals_dict) == 'False'
    # Test bytes
    assert _resolve_index("bytes_val", locals_dict) == "b'test'"
    # Test dict
    assert _resolve_index("dict_val", locals_dict) == "{'key': 'val'}"
    # Test empty list
    assert _resolve_index("empty_list", locals_dict) == "[]"
    # Test multi-space string
    assert _resolve_index("multi_space", locals_dict) == "<SPACE:3>"
    # Test nested index expression
    assert _resolve_index("list_val[i+1]", {"i":1, "list_val":[1,2,3]}) == '3'

def test_resolve_index_empty_or_whitespace():
    """Test _resolve_index with empty or whitespace-only index string"""
    locals_dict = {"i": 0, "j": 1}

    # Test 1: Empty string
    assert _resolve_index("", locals_dict) == "<EMPTY>"
    # Test 2: Whitespace-only string (single space)
    assert _resolve_index(" ", locals_dict) == "<EMPTY>"
    # Test 3: Whitespace-only string (multiple spaces)
    assert _resolve_index("   ", locals_dict) == "<EMPTY>"
    # Test 4: Spaces + tabs 
    assert _resolve_index("\t  ", locals_dict) == "<EMPTY>"

def test_resolve_index_multi_comma():
    """Test _resolve_index with multiple comma-separated indexes"""
    locals_dict = {"i": 0, "j": 1, "k": 2}
    # Test 3 indexes (i,j,k)
    assert _resolve_index("i,j,k", locals_dict) == '(0,1,2)'
    # Test mixed valid/invalid
    assert _resolve_index("i,undefined,k", locals_dict) == "(0,undefined,2)"

# --------------------------
# Test po Function
# --------------------------
def test_po_basic(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test po() basic output with valid frame info"""
    po(123, "test message")
    captured = capsys.readouterr()

    # Verify output format: "42@/test/file.py 123, test message\n"
    assert "42@/test/file.py 123, test message" in captured.out

def test_po_multiple_values(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test po() with multiple values"""
    po(1, 2.5, True, ["a", "b"])
    captured = capsys.readouterr()
    assert "42@/test/file.py 1, 2.5, True, ['a', 'b']" in captured.out

def test_po_conversion_error(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test po() handles string conversion errors"""
    # Create an object that raises TypeError when converted to str
    class BadStrObj:
        def __str__(self):
            raise TypeError("Cannot convert to string")

    po(BadStrObj())
    captured = capsys.readouterr()
    assert "42@/test/file.py [Conversion Error]: Cannot convert to string" in captured.out

def test_po_no_frame(capsys: CaptureFixture[str], mock_no_frame: None):
    """Test po() with missing frame info"""
    po("no frame test")
    captured = capsys.readouterr()
    assert "unknown@unknown no frame test" in captured.out

def test_po_empty_values(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test po() with empty values"""
    po()  # No arguments
    captured = capsys.readouterr()
    assert "42@/test/file.py " in captured.out  # Empty values string

def test_po_special_types(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test po() with special types"""
    # Test bytes/dict/None
    po(b"bytes", {"key": "val"}, None)
    captured = capsys.readouterr()
    assert "42@/test/file.py b'bytes', {'key': 'val'}, None" in captured.out

# --------------------------
# Test pv Function
# --------------------------
def test_pv_simple_variable(capsys: CaptureFixture[str]):
    """Test pv() with simple variable (no indexes)"""
    # Need to execute pv() in a context where inspect can read the caller line
    test_var = "hello pv"
    pv(test_var)  # Line number will vary, focus on variable name and value
    captured = capsys.readouterr()
    assert "test_var = hello pv" in captured.out

def test_pv_single_index(capsys: CaptureFixture[str]):
    """Test pv() with single-level index"""
    i = 0
    test_list = [10, 20, 30]
    pv(test_list[i])  # Should resolve to test_list[0]
    captured = capsys.readouterr()
    assert "test_list[0] = 10" in captured.out

def test_pv_double_index(capsys: CaptureFixture[str]):
    """Test pv() with double-level index"""
    i, j = 1, 0
    test_matrix = [[1,2], [3,4], [5,6]]
    pv(test_matrix[i][j])  # Should resolve to test_matrix[1][0]
    captured = capsys.readouterr()
    assert "test_matrix[1][0] = 3" in captured.out

def test_pv_comma_index(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test pv() with comma-separated index (numpy-style tuple indexing)"""
    # Mock 2D array that supports tuple/index (mimics numpy)
    class Mock2DArray:
        def __getitem__(self, idx: tuple[int, int]):
            if idx == (0, 1):
                return 20
            return None

    # Use values aligned with mock_frame's locals (i=0, j=1)
    i, j = 0, 1
    test_ary = Mock2DArray()

    # Directly mock inspect.getframeinfo to return pre-defined code lines
    # This bypasses the inspect module's internal processing of mock frames
    mock_getframeinfo = Mock(return_value=create_mock_frameinfo(
        code_context=["pv(test_ary[i,j])"]
    ))

    with patch("inspect.getframeinfo", mock_getframeinfo):
        pv(test_ary[i,j])
        captured = capsys.readouterr()
        # Assert matches resolved index values (0,1) from mock_frame's locals
        assert f"test_ary[({i},{j})] = 20" in captured.out
        assert "42@/test/file.py" in captured.out  # Verify location info

def test_pv_no_frame(capsys: CaptureFixture[str], mock_no_frame: None):
    """Test pv() with missing frame info"""
    with patch("inspect.getframeinfo", return_value=mock_no_frame):
        pv("no frame")
        captured = capsys.readouterr()
        assert "unknown@unknown  = no frame" in captured.out

def test_pv_empty_var_name(capsys: CaptureFixture[str]):
    """Test pv() with unparseable variable name"""
    # Mock getframeinfo to return unparseable line
    mock_getframeinfo = create_mock_frameinfo(
        code_context=["pv(   )"]
    )
    with patch("inspect.getframeinfo", return_value=mock_getframeinfo):
        pv(None)
        captured = capsys.readouterr()
        assert "42@/test/file.py  = None" in captured.out

def test_pv_multi_index_expression(capsys: CaptureFixture[str]):
    """Test pv() with complex index expressions"""
    i, j = 1, 2
    test_nested = [[[1,2], [3,4]], [[5,6], [7,8]]]
    pv(test_nested[i-1][j-1])  # Resolves to test_nested[0][1] = [3,4]
    captured = capsys.readouterr()
    assert "test_nested[0][1] = [3, 4]" in captured.out

def test_pv_complex_index_expression(capsys: CaptureFixture[str]):
    """Test pv() with complex index expressions"""
    i = 2
    test_list = [10, 20, 30, 40]
    pv(test_list[i-1])  # Should resolve to test_list[1]
    captured = capsys.readouterr()
    assert "test_list[1] = 20" in captured.out

def test_pv_caller_lines_empty(capsys: CaptureFixture[str]):
    """Test pv() with empty caller lines (unparseable variable name)"""
    # Mock getframeinfo to return empty code context
    mock_getframeinfo = create_mock_frameinfo(
        code_context=[]
    )
    with patch("inspect.getframeinfo", return_value=mock_getframeinfo):
        pv("empty lines test")
        captured = capsys.readouterr()
        assert "42@/test/file.py  = empty lines test" in captured.out

def test_pv_three_level_index(capsys: CaptureFixture[str]):
    """Test pv() with 3-level nested index"""
    i, j, k = 0, 1, 2
    test_3d = [[[1,2,3], [4,5,6]], [[7,8,9], [10,11,12]]]
    pv(test_3d[i][j][k])  # Resolves to test_3d[0][1][2] = 6
    captured = capsys.readouterr()
    assert "test_3d[0][1][2] = 6" in captured.out

# --------------------------
# Test pe Function
# --------------------------
def test_pe_simple_expression(capsys: CaptureFixture[str]):
    """Test pe() with simple arithmetic expression"""
    pe(1 + 2 * 3)  # Should extract "1 + 2 * 3" and show result 7
    captured = capsys.readouterr()
    assert "1 + 2 * 3 = 7" in captured.out

def test_pe_nested_function(capsys: CaptureFixture[str]) -> None:
    """Test pe() with nested function calls"""
    mock_frameinfo = create_mock_frameinfo(
        code_context=["pe(len([1,2,3,4,5]))"]
    )

    # Patch inspect.getframeinfo with our subscriptable mock
    with patch("inspect.getframeinfo", return_value=mock_frameinfo):
        pe(len([1,2,3,4,5]))
        captured = capsys.readouterr()
        assert "42@/test/file.py len([1,2,3,4,5]) = 5" in captured.out

def test_pe_no_frame(capsys: CaptureFixture[str], mock_no_frame: None):
    """Test pe() with missing frame info"""
    pe("test")
    captured = capsys.readouterr()
    assert "unknown@unknown expression = test" in captured.out

def test_pe_empty_expression(capsys: CaptureFixture[str]):
    """Test pe() with empty expression"""
    # Mock unparseable expression
    mock_getframeinfo = create_mock_frameinfo(
        code_context=["pe(   )"]
    )
    with patch("inspect.getframeinfo", return_value=mock_getframeinfo):
        pe(None)
        captured = capsys.readouterr()
        assert "42@/test/file.py  = None" in captured.out

def test_pe_complex_expression(capsys: CaptureFixture[str]):
    """Test pe() with complex nested expression"""
    # Test multi-level nested function
    # Step 1: Create a valid mock FrameInfo object (matches inspect.getframeinfo return type)
    mock_frameinfo = create_mock_frameinfo(
        filename=__file__,
        lineno=420,
        function="test_pe_complex",
        code_context=["pe(sum(filter(lambda x: x>2, [1,2,3,4,5])))"],
        index=0
    )

    # Step 2: Patch the CORRECT getframeinfo target
    with patch("inspect.getframeinfo", return_value=mock_frameinfo):
        # Test multi-level nested function
        pe(sum(filter(lambda x: x>2, [1,2,3,4,5])))

        # Capture output and validat
        captured = capsys.readouterr()
        assert f"420@{__file__} expression = 12" in captured.out
        assert "= 12" in captured.out

def test_pe_multi_line_expression(capsys: CaptureFixture[str]):
    """Test pe() with multi-line expression"""
    # Mock multi-line code context
    mock_getframeinfo = create_mock_frameinfo(
        code_context=["pe(sum([1,2,3]) + len([4,5]))  # Multi-line"]
    )

    with patch("inspect.getframeinfo", return_value=mock_getframeinfo):
        pe(sum([1,2,3]) + len([4,5]))  # 6 + 2 = 8
        captured = capsys.readouterr()
        assert "sum([1,2,3]) + len([4,5]) = 8" in captured.out

def test_pe_regex_match_failure(capsys: CaptureFixture[str]):
    """Test pe() with no regex match (empty exp_name)"""
    # Mock getframeinfo to return invalid line (no pe() match)
    mock_getframeinfo = create_mock_frameinfo(
        code_context=["invalid line without pe()"]
    )
    with patch("inspect.getframeinfo", return_value=mock_getframeinfo):
        pe(123)
        captured = capsys.readouterr()
        assert "42@/test/file.py  = 123" in captured.out

def test_pe_caller_frame_none(capsys: CaptureFixture[str]):
    """Test pe() with caller_frame = None (current_frame has no f_back)"""
    # Mock current frame with no f_back
    mock_current_frame = Mock(spec=types.FrameType)
    mock_current_frame.f_back = None
    mock_current_frame.f_lasti = 0
    with patch("inspect.currentframe", return_value=mock_current_frame):
        pe("caller frame none")
        captured = capsys.readouterr()
        assert "expression = caller frame none" in captured.out

# --------------------------
# Test time_calc Decorator
# --------------------------
def test_time_calc_basic(capsys: CaptureFixture[str], monkeypatch: MonkeyPatch):
    """Test time_calc decorator."""
    # Mock time.time() with fixed values
    time_mock: Mock = Mock()
    time_mock.side_effect = [100.0, 100.5]
    monkeypatch.setattr(time, "time", time_mock)

    # Decorate a test function
    @time_calc
    def test_func() -> str:
        return "test_result"

    # Execute function and verify
    result: str = test_func()
    captured = capsys.readouterr()

    # Verify timing output
    assert "test_func execution time: 0.500000 seconds" in captured.out
    # Verify original function result
    assert result == "test_result"
    # Verify metadata preservation
    assert test_func.__name__ == "test_func"

def test_time_calc_exception(capsys: CaptureFixture[str], monkeypatch: MonkeyPatch):
    """Test time_calc decorator with function that raises exception"""
    time_mock: Mock = Mock()
    time_mock.side_effect = [200.0, 200.75]
    monkeypatch.setattr(time, "time", time_mock)

    @time_calc
    def error_func():
        raise ValueError("Test error")

    # Test exception propagation + timing output
    with pytest.raises(ValueError, match="Test error"):
        error_func()
    captured = capsys.readouterr()
    assert "error_func execution time: 0.750000 seconds" in captured.out

def test_time_calc_zero_time(capsys: CaptureFixture[str], monkeypatch: MonkeyPatch):
    """Test time_calc with zero execution time"""
    time_mock: Mock = Mock()
    time_mock.side_effect = [300.0, 300.0]  # Zero time difference
    monkeypatch.setattr(time, "time", time_mock)

    @time_calc
    def fast_func():
        return "fast"

    _ = fast_func()
    captured = capsys.readouterr()
    assert "fast_func execution time: 0.000000 seconds" in captured.out

# --------------------------
# Test LogLevel Enum
# --------------------------
def test_log_level_enum():
    """Test LogLevel enum values and names"""
    assert LogLevel.INFO == 1
    assert LogLevel.WARN == 2
    assert LogLevel.ERROR == 3
    assert LogLevel.INFO.name == "INFO"
    assert LogLevel.WARN.name == "WARN"
    assert LogLevel.ERROR.name == "ERROR"


# --------------------------
# Test Logit Class
# --------------------------
def test_logit_basic(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit decorator basic logging (INFO level)"""
    # --------------------------
    # Step 1: Mock the timestamp to return a fixed "real" time
    # --------------------------
    # Define your fixed "real" timestamp (e.g., 2026-01-23 12:34:56)
    MOCKED_REAL_TIMESTAMP = "2026-01-23 12:34:56"

    # Mock time.strftime (the function Logit uses to generate timestamps)
    with patch("time.strftime") as mock_strftime:
        # Force strftime to return your fixed timestamp
        mock_strftime.return_value = MOCKED_REAL_TIMESTAMP

        # --------------------------
        # Step 2: Run the Logit test as before
        # --------------------------
        logger = Logit(level=LogLevel.INFO)

        @logger
        def test_func():
            pass

        test_func()
        captured = capsys.readouterr()

        # --------------------------
        # Step 3: Exact assertion with mocked real time
        # --------------------------
        # Assert the EXACT mocked timestamp + location + log message
        expected_log_line = f"{MOCKED_REAL_TIMESTAMP} 042@/test/file.py [INFO]: test_func() was called"
        assert expected_log_line in captured.out

def test_logit_level_filter(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit filters logs below configured level"""
    # Set log level to WARN (ignore INFO)
    logger = Logit(level=LogLevel.WARN)

    # Try to log INFO message (should be filtered)
    logger.info("This INFO message should be ignored")
    captured = capsys.readouterr()
    assert "This INFO message should be ignored" not in captured.out

    # Log WARN message (should be shown)
    logger.warn("This WARN message should be shown")
    captured = capsys.readouterr()
    assert "[WARN]: This WARN message should be shown" in captured.out

def test_logit_file_output(tmp_path: Path, mock_frameinfo: Mock) -> None:
    """Test Logit writes logs to file (updated flow: notify first, then file)"""
    log_file: Path = tmp_path / "test_log.txt"
    logger: Logit = Logit(level=LogLevel.INFO, logfile=str(log_file))

    logger.err("Test error message")

    # Verify file exists and contains log (after notify)
    assert log_file.exists()
    log_content: str = log_file.read_text(encoding="utf8")
    assert "[ERROR]: Test error message" in log_content
    assert "042@/test/file.py" in log_content

def test_logit_notify_called_with_log_str(monkeypatch: MonkeyPatch, mock_frameinfo: Mock) -> None:
    """Test Logit calls _notify with log_str parameter (critical update)"""
    # Mock _notify to capture arguments
    mock_notify: Mock = Mock()
    monkeypatch.setattr(Logit, "_notify", mock_notify)
    
    logger: Logit = Logit()
    test_log_msg: str = "Test notify with log_str"
    logger.info(test_log_msg)
    
    # Verify _notify was called with the correct log_str
    assert mock_notify.called
    call_args = mock_notify.call_args[0][0]  # Get first positional arg (log_str)
    assert test_log_msg in call_args
    assert "[INFO]" in call_args
    assert "042@/test/file.py" in call_args

def test_logit_notify_default_prints_log_str(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit's default _notify prints log_str to console"""
    logger: Logit = Logit()
    test_msg: str = "Test default notify print"
    
    logger.info(test_msg)
    captured = capsys.readouterr()
    
    assert test_msg in captured.out
    assert "[INFO]" in captured.out

def test_logit_error_level(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit ERROR level"""
    logger = Logit(level=LogLevel.ERROR)
    logger.err("Test ERROR log")
    captured = capsys.readouterr()
    assert "[ERROR]: Test ERROR log" in captured.out
    assert "042@/test/file.py" in captured.out

def test_logit_decorator_with_arguments(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit decorator on function with arguments"""
    logger = Logit(level=LogLevel.INFO)

    @logger
    def test_func_with_args(a: int, b: str) -> str:
        return f"{a}{b}"

    # Execute with args
    result = test_func_with_args(123, "test")
    captured = capsys.readouterr()
    assert "[INFO]: test_func_with_args() was called" in captured.out
    assert result == "123test"

def test_logit_decorator_exception(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit decorator on function that raises exception"""
    logger = Logit(level=LogLevel.INFO)

    @logger
    def error_func():
        raise RuntimeError("Test error")

    # Test exception propagation + logging
    with pytest.raises(RuntimeError, match="Test error"):
        error_func()
    captured = capsys.readouterr()
    assert "[INFO]: error_func() was called" in captured.out

def test_logit_empty_logfile(capsys: CaptureFixture[str], mock_frameinfo: Mock):
    """Test Logit with empty logfile (console only via _notify)"""
    logger = Logit(logfile="")
    logger.err("Empty logfile test")
    captured = capsys.readouterr()
    assert "[ERROR]: Empty logfile test" in captured.out

def test_logit_caller_frame_none(capsys: CaptureFixture[str]):
    """Test Logit _log with caller_frame = None (unknown location)"""
    # Mock current frame with no f_back
    mock_current_frame = Mock()
    mock_current_frame.f_back = None
    with patch("inspect.currentframe", return_value=mock_current_frame):
        logger = Logit(level=LogLevel.INFO)
        logger.info("Unknown location test")
        captured = capsys.readouterr()
        assert "unknown@unknown [INFO]: Unknown location test" in captured.out

# --------------------------
# Test EmailLogit Class
# --------------------------
@pytest.mark.parametrize(
    "smtp_server, expected_server, expected_port",
    [
        ("smtp.example.com:587", "smtp.example.com", 587),  # Valid format
        ("smtp.gmail.com: 465 ", "smtp.gmail.com", 465),    # With whitespace
    ],
    ids=["valid_server_port", "valid_server_port_with_whitespace"]
)
def test_email_logit_init_valid_smtp_server(
    smtp_server: str,
    expected_server: str,
    expected_port: int
) -> None:
    """Test EmailLogit.__init__ with valid SMTP server:port format.

    Verifies successful parsing of SMTP server and port from the input string,
    and correct initialization of parent Logit class.

    Args:
        smtp_server: Input SMTP server string (server:port format)
        expected_server: Expected parsed SMTP server name (stripped)
        expected_port: Expected parsed SMTP port (integer)
    """
    # Arrange
    test_email = "recipient@example.com"
    test_username = "sender@example.com"
    test_password = "test_pass_123"
    test_level = LogLevel.WARN

    # Act
    logger = EmailLogit(
        email=test_email,
        username=test_username,
        password=test_password,
        smtp_server=smtp_server,
        level=test_level
    )

    # Assert
    # Verify SMTP attributes are parsed correctly
    assert logger._email == test_email
    assert logger._username == test_username
    assert logger._password == test_password
    assert logger._smtp_server == expected_server
    assert logger._smtp_port == expected_port

    # Verify parent class initialization (disabled file logging)
    assert logger._level == test_level
    assert logger._logfile == ""


@pytest.mark.parametrize(
    "smtp_server, expected_exception, exception_msg_contains",
    [
        (
            "smtp.example.com",  # No port → split into 1 part → IndexError
            IndexError,
            "list index out of range"
        ),
        (
            "smtp.example.com:",  # Empty port → int("") fails
            ValueError,
            "invalid literal for int() with base 10: ''"
        ),
        (
            "smtp.example.com:abc",  # Non-numeric port
            ValueError,
            "invalid literal for int() with base 10: 'abc'"
        ),
    ],
    ids=["no_port", "empty_port", "non_numeric_port"]
)
def test_email_logit_init_invalid_smtp_server(
    smtp_server: str,
    expected_exception: type[Exception],
    exception_msg_contains: str
) -> None:
    """Test EmailLogit.__init__ with invalid SMTP server:port format.

    Verifies that invalid SMTP server strings raise the correct exceptions
    during parsing (IndexError for missing port, ValueError for invalid port).

    Args:
        smtp_server: Invalid SMTP server string
        expected_exception: Type of exception to be raised
        exception_msg_contains: Substring to verify in exception message
    """
    # Arrange
    test_email = "recipient@example.com"
    test_username = "sender@example.com"
    test_password = "test_pass_123"

    # Act & Assert
    with pytest.raises(expected_exception) as excinfo:
        _ = EmailLogit(
            email=test_email,
            username=test_username,
            password=test_password,
            smtp_server=smtp_server
        )

    # Verify exception message contains expected substring
    assert exception_msg_contains in str(excinfo.value)


def test_email_logit_notify_successful_email(capsys: CaptureFixture[str]) -> None:
    """Test EmailLogit._notify with successful email delivery.

    Verifies:
    1. Parent class _notify prints log string to console
    2. SMTP connection is established with correct server/port
    3. Email message is constructed with correct content/headers
    4. SMTP login/send operations are executed
    """
    # Arrange
    logger = EmailLogit(
        email="recipient@example.com",
        username="sender@example.com",
        password="valid_pass",
        smtp_server="smtp.example.com:587",
        level=LogLevel.ERROR
    )

    # Mock SMTP server to simulate successful email send
    with patch("smtplib.SMTP") as mock_smtp:
        # Create mock SMTP server instance
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        test_log_str = "Critical error: Database connection failed"

        # Act
        logger._notify(test_log_str)

        # Assert
        # 1. Verify parent _notify printed log string to console
        captured = capsys.readouterr()
        assert test_log_str in captured.out

        # 2. Verify SMTP connection was created with correct parameters
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)

        # 3. Verify SMTP TLS/login/send operations were executed
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@example.com", "valid_pass")

        # 4. Verify email message was constructed correctly
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg['From'] == "sender@example.com"
        assert sent_msg['To'] == "recipient@example.com"
        assert sent_msg['Subject'] == "[ERROR] Log Alert"
        assert f"Log Notification: {test_log_str}" in sent_msg.get_payload()


def test_email_logit_notify_smtp_exception(capsys: CaptureFixture[str]) -> None:
    """Test EmailLogit._notify with SMTP-related errors (SMTPException).

    Verifies that SMTP errors (e.g., authentication failure) are caught and
    the correct error message is printed to console.
    """
    # Arrange
    logger = EmailLogit(
        email="recipient@example.com",
        username="sender@example.com",
        password="wrong_pass",  # Invalid password to trigger SMTP error
        smtp_server="smtp.example.com:587"
    )

    # Mock SMTP server to raise authentication error
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        # Simulate SMTP authentication failure
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            code=535,
            msg="Invalid credentials"
        )

        test_log_str = "Test SMTP authentication error"

        # Act
        logger._notify(test_log_str)

        # Assert
        captured = capsys.readouterr()
        # 1. Verify parent _notify output
        assert test_log_str in captured.out

        # 2. Verify SMTPException error message is printed
        expected_error_msg = (
            "[Email Notification Error]: SMTPAuthenticationError: (535, 'Invalid credentials')"
        )
        assert expected_error_msg in captured.out


def test_email_logit_notify_generic_exception(capsys: CaptureFixture[str]) -> None:
    """Test EmailLogit._notify with unexpected generic exceptions.

    Verifies that non-SMTP exceptions are caught by the generic Exception handler
    and the correct error message is printed to console.
    """
    # Arrange
    logger = EmailLogit(
        email="recipient@example.com",
        username="sender@example.com",
        password="valid_pass",
        smtp_server="smtp.example.com:587"
    )

    # Mock SMTP to raise an unexpected error (AttributeError)
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        # Simulate unexpected error during send_message
        mock_server.send_message.side_effect = AttributeError("Invalid message format")

        test_log_str = "Test unexpected error during email send"

        # Act
        logger._notify(test_log_str)

        # Assert
        captured = capsys.readouterr()
        # 1. Verify parent _notify output
        assert test_log_str in captured.out

        # 2. Verify generic Exception error message is printed
        expected_error_msg = (
            "[Email Notification Unexpected Error]: AttributeError: Invalid message format"
        )
        assert expected_error_msg in captured.out


def test_email_logit_notify_smtp_connection_failure(capsys: CaptureFixture[str]) -> None:
    """Test EmailLogit._notify with SMTP connection timeout error.

    Additional edge case: Verifies SMTP connection failures are caught by SMTPException.
    """
    # Arrange
    logger = EmailLogit(
        email="recipient@example.com",
        username="sender@example.com",
        password="valid_pass",
        smtp_server="invalid.server.com:587"
    )

    # Mock SMTP to raise connection error
    with patch("smtplib.SMTP") as mock_smtp:
        # Raise SMTPConnectError when SMTP class is initialized
        mock_smtp.side_effect = smtplib.SMTPConnectError(
            code=421,
            msg="Cannot connect to SMTP server"
        )

        test_log_str = "Test SMTP connection failure"

        # Act
        logger._notify(test_log_str)

        # Assert
        captured = capsys.readouterr()
        # 1. Verify parent _notify output
        assert test_log_str in captured.out

        # 2. Verify SMTPException error message
        expected_error_msg = (
            "[Email Notification Error]: SMTPConnectError: (421, 'Cannot connect to SMTP server')"
        )
        assert expected_error_msg in captured.out


if __name__ == "__main__":
    pytest_args: list[str] = ["-v", __file__, "--cov=src.pyutilities.logit"]
    _ = pytest.main(pytest_args)
