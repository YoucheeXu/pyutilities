#!/usr/bin/env python3
import sys
import re
import subprocess
from pathlib import Path

def extract_test_command_from_file(file_path: Path) -> str | None:
    """Extract the uv pytest command from the module-level comment of a test file.

    Parses the triple-quoted module comment to find a pytest command starting with
    "uv run pytest", cleans up whitespace/newlines, and returns the command string.

    Args:
        file_path: Path to the test file (e.g., tests/test_gvar.py).

    Returns:
        Extracted test command string (e.g., "uv run pytest --cov=xxx ...") if found;
        None if no valid comment/command is found, or if an error occurs.

    Raises:
        Exception: Catches and logs all file reading/parsing errors (no explicit raise).
    """
    try:
        # Read file content with UTF-8 encoding (supports non-ASCII characters)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to match module-level triple-quoted comments (supports """ and ''')
        # Captures content inside triple quotes, ignoring leading/trailing whitespace
        comment_pattern = r'^[\'"]{3}(.*?)[\'"]{3}'
        comment_match = re.search(comment_pattern, content, re.DOTALL | re.MULTILINE)

        if not comment_match:
            print(f"⚠️ {file_path.name}: No module-level triple-quoted comment found")
            return None

        # Clean comment content (remove newlines and extra whitespace)
        comment_content = comment_match.group(1).strip()

        # Extract command starting with "uv run pytest" (ignore newlines/spaces)
        cmd_pattern = r'(uv run pytest .+?)(?=\n|$)'
        cmd_match = re.search(cmd_pattern, comment_content, re.DOTALL)

        if not cmd_match:
            print(f"⚠️ {file_path.name}: No 'uv run pytest' command found in comment")
            return None

        # Clean the command (merge newlines, remove extra spaces)
        test_cmd = re.sub(r'\s+', ' ', cmd_match.group(1)).strip()
        return test_cmd

    except Exception as e:
        print(f"❌ {file_path.name}: Failed to read/parse - {str(e)}")
        return None

def find_test_files(tests_dir: Path) -> list[Path]:
    """Recursively find all .py files starting with 'test' in the tests directory.

    Validates the existence of the tests directory and returns a list of valid test files.
    Logs warnings if no test files are found.

    Args:
        tests_dir: Root directory of test files.

    Returns:
        List of Path objects for valid test files (test*.py). Exits with code 1 if the
        tests directory does not exist.
    """
    if not tests_dir.exists():
        print(f"❌ Error: Test directory {tests_dir} does not exist!")
        sys.exit(1)

    # Recursively find files: starts with 'test' + .py extension
    test_files = list(tests_dir.glob("**/test*.py"))
    if not test_files:
        print(f"⚠️ Warning: No .py files starting with 'test' found in {tests_dir}")
        return []

    print(f"✅ Found {len(test_files)} test file(s):")
    for f in test_files:
        print(f"  - {f.relative_to(tests_dir)}")
    print("-" * 50)
    return test_files

def execute_test_command(cmd: str, file_name: str) -> bool:
    """Execute an extracted test command and return execution status.

    Runs the pytest command, streams output to the console, and returns whether
    the command succeeded (exit code 0) or failed (non-zero exit code).

    Args:
        cmd: Test command string to execute (e.g., "uv run pytest --cov=xxx ...").
        file_name: Name of the test file (for logging purposes).

    Returns:
        True if the command executes successfully; False if it fails.
    """
    print(f"\n🚀 Executing test command for {file_name}:")
    print(f"   Command: {cmd}")

    try:
        # Split command into parts (handles space-separated arguments correctly)
        # cmd_parts = subprocess.list2cmdline(cmd).split()
        # Execute command and capture output (inherit terminal output)
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=Path(__file__).parent.parent,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        # Print execution results
        print(f"✅ {file_name} tests passed!")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ {file_name} tests failed!")
        print(f"   Error output: {e.stdout.strip()}")
        return False

def run_all_tests():
    """Main function: Orchestrate execution of all test file commands.

    Coordinates the full workflow:
    1. Locate the tests directory
    2. Find all valid test files (test*.py)
    3. Extract and execute test commands for each file
    4. Generate a summary of pass/fail results
    5. Exit with code 1 if any tests fail (for CI/CD integration)
    """
    # 1. Locate the tests directory
    tests_dir = Path("./tests")

    # 2. Find all test files starting with 'test'
    test_files = find_test_files(tests_dir)
    if not test_files:
        sys.exit(0)

    # 3. Iterate over files, extract and execute test commands
    results: list[tuple[Path, bool]] = []  # (file_path, execution_success)
    for file_path in test_files:
        # Extract command from file
        test_cmd = extract_test_command_from_file(file_path)
        if not test_cmd:
            results.append((file_path, False))
            continue

        # Execute the extracted command
        success = execute_test_command(test_cmd, file_path.name)
        results.append((file_path, success))

    # 4. Generate test result summary
    print("\n" + "=" * 60)
    print("📊 Test Result Summary:")
    success_count = sum(1 for _, success in results if success)
    fail_count = len(results) - success_count

    print(f"✅ Passed: {success_count} file(s)")
    print(f"❌ Failed: {fail_count} file(s)")

    if fail_count > 0:
        print("\n💥 List of failed files:")
        for file_path, success in results:
            if not success:
                print(f"   - {file_path.relative_to(tests_dir)}")
        sys.exit(1)  # Return non-zero exit code for CI/CD failure detection
    else:
        print("\n🎉 All test files executed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
