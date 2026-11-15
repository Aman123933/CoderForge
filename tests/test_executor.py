import pytest
from backend.app.tools.execution_tools import SafePythonExecutor


def test_executor_successful_run():
    executor = SafePythonExecutor(timeout=3.0)
    res = executor.execute("print('Hello CodeForge')")
    assert res["success"] is True
    assert res["exit_code"] == 0
    assert "Hello CodeForge" in res["output"]
    assert res["duration"] >= 0.0


def test_executor_timeout_enforced():
    executor = SafePythonExecutor(timeout=0.5)
    res = executor.execute("import time; time.sleep(2)")
    assert res["success"] is False
    assert res["exit_code"] == 124
    assert "timed out" in res["stderr"].lower() or "timed out" in (res.get("error") or "").lower()


def test_executor_blocked_network():
    executor = SafePythonExecutor(timeout=3.0, allow_network=False)
    code = (
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    )
    res = executor.execute(code)
    assert res["success"] is False
    assert "Network access is disabled" in res["stderr"]


def test_executor_multi_file_project():
    executor = SafePythonExecutor(timeout=3.0)
    project = {
        "helper.py": "def greet(name):\n    return f'Hello, {name}!'\n",
        "main.py": "from helper import greet\nprint(greet('CodeForge'))\n",
    }
    manifest = {"entrypoint": "main.py", "files": ["helper.py", "main.py"]}
    res = executor.execute_project(project, manifest=manifest)
    assert res["success"] is True
    assert res["exit_code"] == 0
    assert "Hello, CodeForge!" in res["output"]


def test_executor_syntax_error():
    executor = SafePythonExecutor(timeout=3.0)
    res = executor.execute("def invalid_syntax(")
    assert res["success"] is False
    assert res["exit_code"] != 0
    assert "SyntaxError" in res["stderr"]
