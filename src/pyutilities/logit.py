#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
Python Debugging & Logging Utility Toolkit
==========================================
Core Features:
- Enhanced print functions (po/pv/pe) with caller context (line number + filename)
- Function execution time calculator (time_calc decorator)
- Extensible class-based logging decorator (Logit) with log levels and file output
- Inheritable logging extension (EmailLogit) for notification integration

Dependencies:
- inspect: For retrieving call stack/frame metadata (core for context awareness)
- re: For regex-based variable/expression parsing from caller code
- time: For timestamp generation and execution time measurement
- enum: For typed log level definitions
- functools.wraps: For preserving original function metadata in decorators
- typing: For type hints (improves maintainability and IDE support)

Usage Notes:
- Frame references are explicitly deleted to prevent memory leaks
- Log levels follow IntEnum (higher value = more severe: INFO < WARN < ERROR)
"""
# Standard library imports with purpose annotations
import re                          # Regular expressions for parsing variable/expression strings
import inspect                     # Access call stack/frame info (caller line, filename, locals)
import time                        # Time utilities (timestamps, execution time measurement)
from enum import IntEnum           # Typed enumeration for log levels (type-safe vs. plain integers)
from functools import wraps        # Preserve original function metadata in decorators
from typing import override        # Mark method overrides (type hint for inheritance)
from typing import (
    Callable,                      # Type hint for callable objects (functions/methods)
    TypeVar,                       # Generic type variable for flexible type hints
    ParamSpec,                     # Generic type for function parameter specifications
)


# ------------------------------------------------------------------------------
# Generic Type Definitions (for type-safe decorators/functions)
# ------------------------------------------------------------------------------
# Generic type variable representing any arbitrary type
T = TypeVar('T')

# Generic type variable for index values (used in _resolve_index)
V = TypeVar('V')

# Parameter specification (P) and return type (R) for decorator type safety
# P: Captures all positional/keyword parameters of a function
# R: Captures the return type of a function
P = ParamSpec("P")
R = TypeVar("R")


def _get_caller_location(skipframe: int = 2):
    """ get caller location according skipframe

    Args:
        skipframe: the frame number to skip

    Returns:
        (caller_lineno, caller_filename)

    """
    # Initialize location variables (None = unknown location)
    caller_filename: str = "unknown"
    caller_lineno: int | str = "unknown"

    caller_frame = inspect.currentframe()
    try:
        for _ in range(skipframe):
            caller_frame = caller_frame.f_back

        # Extract caller metadata if frame is available
        if caller_frame:
            frame_info = inspect.getframeinfo(caller_frame)
            # Full path to caller file
            caller_filename = frame_info.filename
            # Line number of caller
            caller_lineno = frame_info.lineno
    except:
        pass
    finally:  # Release frame reference (critical for memory management)
        if caller_frame:
            del caller_frame
        return (caller_lineno, caller_filename)

# ------------------------------------------------------------------------------
# Enhanced Print Functions
# ------------------------------------------------------------------------------
def po(*values: object, endstr: str = "\n") -> None:
    """ Print values with caller location info (line number @ filename)
    Handles string conversion exceptions to prevent tool crashes during debugging

    Args:
        *values: Variable-length argument list of objects to print (any type)
        endstr: Trailing character for the print statement (default: newline)

    Returns:
        None

    Error Handling:
        Catches TypeError/ValueError/OverflowError during string conversion
        and returns a user-friendly error message instead of crashing.

    Memory Notes:
        Explicitly deletes frame references to avoid cyclic references/memory leaks.

    """
    # Get location (use DEFAULT skip_frames=2: code -> this po() function → actual caller)
    lineno, filename = _get_caller_location()
    location_str = f"{lineno}@{filename}"

    # Convert values to string with exception handling
    try:
        # Join multiple values into a single string (e.g., po(1, "test") → "1, test")
        # values_str = ", ".join(str(arg) for arg in args)
        # output_str = ", ".join(map(str, values))
        output_str = ", ".join(str(arg) for arg in values) if values else ""
    except (TypeError, ValueError, OverflowError) as e:
        # Catch common exceptions during string conversion:
        # TypeError - type does not support str() conversion
        # ValueError - invalid value during conversion
        # OverflowError - numeric value is too large to convert
        output_str = f"[Conversion Error]: {e}"

    # Print final output (location + values)
    print(f"{location_str} {output_str}", end=endstr)


def _resolve_index(index_str: str, locals_dict: dict[str, V]) -> str:
    """ Resolve index string with variables/expressions to actual values
    Converts variable references/expressions to their stringified values (e.g., i=5 → "5").
    Enhanced: Clearly distinguish empty strings ("") from space-only strings ("  ") with unique markers.
    Handles comma-separated indexes (e.g. "i,j" → "(0,1)")

    Args:
        index_str: Index expression string (e.g., "i", "i+1", "5")
        locals_dict: Caller's local variables (from caller_frame.f_locals)

    Returns:
        Resolved index value (or original expression if resolution fails)
        - Empty string ("") → "<EMPTY>"
        - Space-only string ("  ") → "<SPACE:N>" (N = number of spaces)
        - Normal strings → quoted (e.g., "  test  " → "'  test  '")
        - Other values → regular string (e.g., 5 → "5", None → "None")

    WARNING: Uses eval() directly - DO NOT use with untrusted input!
    """
    # Helper: Special string formatting for empty/space-only strings
    def format_special_string(value: V) -> str:
        """ Format values to distinguish string types from non-str types.
        
        Args:
            value: Original value (before string conversion)
        
        Returns:
            Formatted string with special markers for empty/space-only strings
        """
        # Case 1: Non-string values (int, None, float, etc.) → direct string conversion
        if not isinstance(value, str):
            return str(value)

        # Case 2: Exact empty string ("")
        if value == "":
            return "<EMPTY>"

        # Case 3: String with only whitespace (spaces/tabs/newlines)
        stripped = value.strip()
        if stripped == "":
            return f"<SPACE:{len(value)}>"  # Mark space count (e.g., "<SPACE:2>")
        
        # Case 4: Normal string (has non-whitespace content) → quote it
        return f"'{value}'"

    # Step 1: Handle empty index input (after stripping whitespace)
    if not index_str.strip():
        return "<EMPTY>"

    # Step 2: Evaluate expression (preserve original type)
    # Handle comma-separated indexes first (numpy-style tuple indexing)
    if "," in index_str:
        parts = [p.strip() for p in index_str.split(",")]
        resolved_parts = []
        for part in parts:
            try:
                # Get actual value (e.g., "i" → 0(int))
                resolved_val = eval(part, globals(), locals_dict)
                resolved_parts.append(format_special_string(resolved_val))
            # Step 3: Handle evaluation failures (return original expression formatted)
            except (NameError, TypeError, ValueError, SyntaxError) as e:
                po(f"{index_str} eval error: {e}")
                resolved_parts.append(part)
        return f"({','.join(resolved_parts)})"

    # Handle single index/expression
    try:
        # Evaluate simple expressions (e.g. "i+1", "len(list)")
        resolved_val = eval(index_str, globals(), locals_dict)
        return format_special_string(resolved_val)
    except:
        # Return original if evaluation fails
        return index_str

def pv(*args: object, endstr: str = "\n") -> None:
    """ Print variable name (with resolved indexes), value, and caller location
    Supports multi-level/indexed variables (e.g., a[i][j], a[i,j], a[i]).

    Args:
        args: Variable/value to print (can be any object, including indexed collections)
        endstr: Trailing character for the print statement (default: newline)

    Returns:
        None

    Key Features:
        1. Extracts variable name from caller code (via regex)
        2. Resolves index variables to their actual values (e.g., i=5 → a[5])
        3. Handles 3 index formats: double-level (a[i][j]), comma-separated (a[i,j]), single-level (a[i])
        4. Preserves memory safety (deletes frame references)
    """
    # Initialize variable name (empty = not found)
    location_str: str = "unknown@unknown"
    var_name: str = ""

    # Get current/ caller frames
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back if current_frame else None

    if caller_frame:
        # Get caller location (lineno@filename)
        frame_info = inspect.getframeinfo(caller_frame)
        location_str = f"{frame_info.lineno}@{frame_info.filename}"

        # Extract caller code lines (list of lines where pv() was called)
        # caller_code_lines = inspect.getframeinfo(caller_frame)[3]
        caller_code_lines = frame_info.code_context or []
        if caller_code_lines:
            # Iterate through caller lines to find pv() invocation
            for line in caller_code_lines:
                 # Clean line: remove comments (everything after #) and extra whitespace
                cleaned_line = re.sub(r"#.*$", "", line).strip()
                # Regex pattern to match pv(...) (supports spaces inside parentheses)
                # Matches: pv(var), pv( var ), pv(var, end=""), pv( var , end='')
                # pv_pattern = r'\bpv\s*\(\s*(.+?)\s*(?:,|)\s*\)'
                pv_pattern = r"pv\(\s*(.+?)\s*\)"
                if match := re.search(pv_pattern, cleaned_line):
                    # Extract variable name (ignore end= parameter if present)
                    var_name = match.group(1).split(", end")[0].strip()
                    break   # Stop after first match (avoids multiple line false positives)

        # --------------------------
        # Universal Index Resolution (All Formats)
        # --------------------------
        # Extract all index parts using regex (works for all formats)
        index_matches = re.findall(r"\[(.*?)\]", var_name)
        if index_matches and var_name:
            # Get base name (everything before first [)
            base_name = var_name.split("[")[0]
            resolved_indexes = []

            # Resolve each index part individually
            for idx_part in index_matches:
                resolved_idx = _resolve_index(idx_part, caller_frame.f_locals)
                resolved_indexes.append(f"[{resolved_idx}]")
            
            # Rebuild variable name with resolved indexes
            var_name = base_name + "".join(resolved_indexes)

    if current_frame:
        del current_frame
    if caller_frame:
        del caller_frame 

    # Print final output
    value_str = ", ".join(str(arg) for arg in args) if args else ""
    print(f"{location_str} {var_name} = {value_str}", end=endstr)


def pe(exp: object, end: str = "\n") -> None:
    """ Print expression and its evaluated result (debugging-focused).
    Extracts the original expression string from caller code (supports nested functions).

    Args:
        exp: Evaluated expression result (any object)
        end: Trailing character for the print statement (default: newline)

    Returns:
        None

    Key Features:
        1. Uses balanced parentheses regex to handle nested functions (e.g., pe(len(filter(...))))
        2. Extracts original expression string from caller code
        3. Gracefully handles missing frame info (uses "expression" as fallback name)
    """
    # Initialize expression name (fallback = "expression")
    exp_name: str = "expression"
    location_str: str = "unknown@unknown"

    # Get current/caller frame
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back if current_frame else None

    if caller_frame:
        frame_info = inspect.getframeinfo(caller_frame)
        location_str = f"{frame_info.lineno}@{frame_info.filename}"

        # Extract caller code lines
        # caller_code_lines = inspect.getframeinfo(caller_frame)[3]
        caller_code_lines = frame_info.code_context or []

        if caller_code_lines:
            # Regex pattern for balanced parentheses (handles nested functions)
            # Matches: pe(any_expression) where any_expression can have nested ()
            pattern = r"\bpe\s*\(([^()]*+(?:\([^()]*+\)[^()]*+)*+)\)"
            # pe_pattern = r"pe\(\s*((?:[^()]+|\((?:[^()]+|\([^()]*\))*\))*)\s*\)"

            # Iterate through caller lines to find pe() invocation
            for line in caller_code_lines:
                # Clean line: remove comments and extra whitespace
                cleaned_line = re.sub(r"#.*$", "", line).strip()
                # Match pe() expression
                if match := re.search(pattern, cleaned_line):
                    # Extract expression (remove trailing commas if present)
                    exp_name = match.group(1).rstrip(',').strip()
                    break   # Stop after first match

    # Clean up frame references (memory safety)
    if caller_frame:
        del caller_frame
    if current_frame:
        del current_frame

    # Print final output
    print(f"{location_str} {exp_name} = {exp}", end=end)


# ------------------------------------------------------------------------------
# Execution Time Decorator
# ------------------------------------------------------------------------------
def time_calc(func: Callable[P, R]) -> Callable[P, R]:
    """ Decorator to measure and print a function's execution time.
    Preserves original function metadata (name, docstring, signature) via @wraps.

    Args:
        func: Function to decorate (any callable with parameters P and return type R)

    Returns:
        Callable[P, R]: Wrapped function with timing logic

    Features:
        1. Precise timing (6 decimal places for seconds)
        2. No side effects (returns original function's result)
        3. Preserves function metadata (critical for debugging/introspection)
    """
    # Preserve original function metadata (prevents loss of __name__, __doc__, etc.)
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Record start time (Unix timestamp in seconds)
        start_time = time.time()
        try:
            # Execute the original function (pass all positional/keyword args)
            # Return original function result (no side effects)
            return func(*args, **kwargs)
        finally:
            # Calculate elapsed time
            end_time = time.time()
            exec_time = end_time - start_time
            # Print execution time (6 decimal places for precision)
            print(f"{func.__name__} execution time: {exec_time:.6f} seconds")
    return wrapper


# ------------------------------------------------------------------------------
# Logging System (Class-Based Decorator)
# ------------------------------------------------------------------------------
class LogLevel(IntEnum):
    """ Enumeration for log severity levels (typed for safety).
    Higher integer values = more severe log levels.

    Attributes:
        INFO: General informational messages (default)
        WARN: Warning messages (non-critical issues)
        ERROR: Error messages (critical failures)
    """
    # Lowest severity: general info (e.g., "Function X called")
    INFO = 1
    # Medium severity: warnings (e.g., "Low memory")
    WARN = 2
    # Highest severity: errors (e.g., "File not found")
    ERROR = 3


class Logit():
    """ Class-based decorator for flexible logging with context-aware metadata.
    Core features: log levels, timestamped output, file logging, and extensibility.

    Design Notes:
        - Implements __call__ to act as a decorator
        - Uses composition over inheritance (easily extendable via subclasses)
        - Separates core logging logic (_log) from notification logic (_notify)
        - Memory-safe (deletes frame references to prevent leaks)

    Attributes:
        _level: Minimum log level to output (e.g., LogLevel.WARN → ignore INFO)
        _logfile: Path to log file (empty = no file output)
    """
    def __init__(self, level: LogLevel = LogLevel.INFO, logfile: str = ""):
        """ Initialize Logit decorator with log level and file path.

        Args:
            level: Minimum log severity to output (default: LogLevel.INFO)
            logfile: Path to log file (empty string = disable file logging)
        """
        self._level: LogLevel = level
        self._logfile: str = logfile

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """ Make Logit a decorator: wrap target function with logging logic.
        Logs a "function called" message before executing the target function.

        Args:
            func: Function to decorate (any callable with parameters P and return type R)

        Returns:
            Callable[P, R]: Wrapped function with logging logic
        """
        # Preserve original function metadata
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Log function invocation (uses decorator's configured log level)
            self._log(self._level, f"{func.__name__}() was called")
            # Execute original function and return result
            return func(*args, **kwargs)
        return wrapper  # Return wrapped function

    def _notify(self, log_str: str):
        """Reserved extension point for notifications (e.g., email, SMS)
        Override this method in subclasses to add notification logic (no-op by default).

        Args:
            log_str: Human-readable log message string
        """
        # Print to console
        print(log_str)

    def _log(self, level: LogLevel, msg: str):
        """ Core logging logic: format and output log messages (console + file).
        Only processes logs with severity ≥ self._level (e.g., WARN ignores INFO).

        Args:
            level: Severity level of the log message (LogLevel enum)
            msg: Human-readable log message string

        Key Steps:
            1. Check log level threshold
            2. Generate timestamp and caller location
            3. Format log string (timestamp + location + level + message)
            4. Output to console
            5. Write to log file (if configured)
            6. Trigger notification (via _notify)
        """
        # Skip logs below the configured severity level
        if level < self._level:
            return

        # --------------------------
        # Generate Log Metadata
        # --------------------------
        # Human-readable timestamp (YYYY-MM-DD HH:MM:SS)
        timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        lineno, filename = _get_caller_location(3)
        if isinstance(lineno, int):
            location_str = f"{lineno:03d}@{filename}"
        else:
            location_str = f"{lineno}@{filename}"

        # --------------------------
        # Format & Output Log
        # --------------------------
        # Use level NAME (e.g., "INFO") instead of integer for readability
        log_str = f"{timestr} {location_str} [{level.name}]: {msg}"

        # Trigger notification logic (extension point)
        self._notify(log_str)

        # Write to log file if path is provided
        if self._logfile:
            # Use UTF-8 encoding to support non-ASCII characters
            # Append mode ("a") to preserve existing logs
            with open(self._logfile, 'a', encoding='utf8') as opened_file:
                # Write log string + newline (ignore return value with _)
                _ = opened_file.write(log_str + '\n')

    # --------------------------
    # Convenience Methods (Log Level Shortcuts)
    # --------------------------
    def info(self, msg: str):
        """Shortcut method to log an INFO-level message."""
        self._log(LogLevel.INFO, msg)

    def warn(self, msg: str):
        """Shortcut method to log a WARN-level message."""
        self._log(LogLevel.WARN, msg)

    def err(self, msg: str):
        """Shortcut method to log an ERROR-level message."""
        self._log(LogLevel.ERROR, msg)


class EmailLogit(Logit):
    """ Inherited Logit decorator with email notification support.
    Extends base Logit by overriding _notify() to send emails on log events.

    Additional Attributes:
        _email: Recipient email address for notifications
        _username: user name for emali login
        _password: password for emali login
        _smtp_server: smtp server without port, (e.g., "smtp.example.com")
        _smtp_port: smtp server port, (e.g., "587")
    """
    def __init__(
        self, 
        email: str, 
        username: str, 
        password: str, 
        smtp_server: str,
        level: LogLevel = LogLevel.INFO
    ):
        """ Initialize EmailLogit with recipient email and log level.

        Args:
            email: Recipient email address (e.g., "dev@example.com")
            username: user name for emali login
            password: password for emali login
            smtp_server: smtp server with port, (e.g., "smtp.example.com: 587")
            level: Minimum log severity to output (default: LogLevel.INFO)
        """
        # Store email/smtp credentials (used in _notify)
        self._email: str = email
        self._username: str = username
        self._password: str = password

        # Parse SMTP server/port
        server_parts = smtp_server.split(":")
        self._smtp_server: str = server_parts[0].strip()
        self._smtp_port: int = int(server_parts[1].strip())

        # Call parent class constructor (disable file logging by default)
        super().__init__(level, "")

    @override
    def _notify(self, log_str: str):
        """ Override parent _notify() to implement email sending logic.
        Placeholder implementation (replace with actual email code in production).

        Implementation Notes:
            - Use smtplib/email libraries to send emails
            - Include log details (timestamp, level, message) in email body
            - Add error handling for email delivery failures
        """
        # Always print to console first
        super()._notify(log_str)

        import smtplib
        from email.mime.text import MIMEText
        try:
            # Create email message
            msg = MIMEText(f"Log Notification: {log_str}")
            msg['Subject'] = f"[{self._level.name}] Log Alert"
            msg['From'] = self._username
            msg['To'] = self._email

            # SMTP connection
            with smtplib.SMTP(self._smtp_server, self._smtp_port, timeout=10) as server:
                _ = server.starttls()  # Enforce TLS (security)
                _ = server.login(self._username, self._password)
                _ = server.send_message(msg)
        except smtplib.SMTPException as e:
            # Catch all SMTP-related errors (connection, login, send)
            print(f"[Email Notification Error]: {type(e).__name__}: {str(e)}")
        except Exception as e:
            # Catch-all for unexpected errors
            print(f"[Email Notification Unexpected Error]: {type(e).__name__}: {str(e)}")
