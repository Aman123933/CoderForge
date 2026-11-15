import io
import sys
import traceback
from typing import Dict, Any


class SafePythonExecutor:
    """
    Executes Python code in a restricted environment.
    """

    def execute(self, code: str) -> Dict[str, Any]:
        stdout = io.StringIO()
        stderr = io.StringIO()

        restricted_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "dict": dict,
                "list": list,
            }
        }

        try:
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            sys.stdout = stdout
            sys.stderr = stderr

            exec(code, restricted_globals, {})

            return {
                "success": True,
                "output": stdout.getvalue(),
                "error": None,
            }

        except Exception:
            return {
                "success": False,
                "output": stdout.getvalue(),
                "error": traceback.format_exc(),
            }

        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
