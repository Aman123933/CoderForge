import os
import sys
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Union, Optional


class SafePythonExecutor:
    """
    Executes Python code or multi-file projects in a sandboxed subprocess
    with timeout (10s), temp directory, resource constraints, and blocked network.
    """

    def __init__(
        self,
        timeout: float = 10.0,
        memory_limit_mb: int = 256,
        allow_network: bool = False,
    ):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.allow_network = allow_network
        self.docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        docker_cmd = shutil.which("docker")
        if not docker_cmd:
            return False
        try:
            res = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=2,
            )
            return res.returncode == 0
        except Exception:
            return False

    def execute(
        self,
        code_or_project: Union[str, Dict[str, str]],
        entrypoint: str = "main.py",
        manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes code or a dict of files (path -> code) in a sandboxed subprocess.
        """
        if self.docker_available:
            return self._execute_in_docker(code_or_project, entrypoint=entrypoint, manifest=manifest)
        return self._execute_in_subprocess(code_or_project, entrypoint=entrypoint, manifest=manifest)

    def execute_project(
        self,
        project: Dict[str, str],
        manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        entrypoint = "main.py"
        if manifest and manifest.get("entrypoint"):
            entrypoint = manifest["entrypoint"]
        elif "main.py" in project:
            entrypoint = "main.py"
        elif project:
            entrypoint = next(iter(project.keys()))
        return self.execute(project, entrypoint=entrypoint, manifest=manifest)

    def _execute_in_subprocess(
        self,
        code_or_project: Union[str, Dict[str, str]],
        entrypoint: str = "main.py",
        manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory(prefix="codeforge_exec_") as temp_dir:
            temp_path = Path(temp_dir).resolve()

            # 1. Write project files
            if isinstance(code_or_project, dict):
                for rel_path, content in code_or_project.items():
                    target_file = (temp_path / rel_path).resolve()
                    # Prevent directory traversal
                    if not str(target_file).startswith(str(temp_path)):
                        continue
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(content, encoding="utf-8")
            else:
                main_file = temp_path / entrypoint
                main_file.parent.mkdir(parents=True, exist_ok=True)
                main_file.write_text(str(code_or_project), encoding="utf-8")

            # 2. Add network-blocking hook via sitecustomize.py if network is disabled
            if not self.allow_network:
                sitecustomize = temp_path / "sitecustomize.py"
                blocker_code = (
                    "import socket\n"
                    "def _blocked(*args, **kwargs):\n"
                    "    raise PermissionError('Network access is disabled in CodeForge sandbox')\n"
                    "socket.socket = _blocked\n"
                    "socket.create_connection = _blocked\n"
                    "socket.getaddrinfo = _blocked\n"
                )
                sitecustomize.write_text(blocker_code, encoding="utf-8")

            # 3. Prepare entrypoint script
            exec_entrypoint = temp_path / entrypoint
            if not exec_entrypoint.exists():
                # Fallback to any python file found
                py_files = list(temp_path.glob("*.py"))
                py_files = [f for f in py_files if f.name != "sitecustomize.py"]
                if py_files:
                    exec_entrypoint = py_files[0]
                else:
                    duration = time.perf_counter() - start_time
                    return {
                        "success": False,
                        "output": "",
                        "stderr": f"Entrypoint '{entrypoint}' not found in project",
                        "exit_code": 1,
                        "duration": round(duration, 4),
                        "error": f"Entrypoint '{entrypoint}' not found",
                    }

            # 4. Prepare restricted environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(temp_path)
            env["PYTHONUNBUFFERED"] = "1"
            if not self.allow_network:
                env["HTTP_PROXY"] = "http://127.0.0.1:0"
                env["HTTPS_PROXY"] = "http://127.0.0.1:0"
                env["ALL_PROXY"] = "http://127.0.0.1:0"
                env["NO_PROXY"] = ""

            # 5. Execute process with timeout
            try:
                proc = subprocess.run(
                    [sys.executable, str(exec_entrypoint)],
                    cwd=str(temp_path),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                duration = time.perf_counter() - start_time
                stdout = proc.stdout or ""
                stderr = proc.stderr or ""
                success = (proc.returncode == 0)

                return {
                    "success": success,
                    "output": stdout,
                    "stderr": stderr,
                    "exit_code": proc.returncode,
                    "duration": round(duration, 4),
                    "error": stderr if not success else None,
                }

            except subprocess.TimeoutExpired as e:
                duration = time.perf_counter() - start_time
                stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
                stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
                return {
                    "success": False,
                    "output": stdout,
                    "stderr": f"Process timed out after {self.timeout}s\n" + str(stderr),
                    "exit_code": 124,
                    "duration": round(duration, 4),
                    "error": f"Execution timed out after {self.timeout}s",
                }

            except Exception as e:
                duration = time.perf_counter() - start_time
                return {
                    "success": False,
                    "output": "",
                    "stderr": str(e),
                    "exit_code": 1,
                    "duration": round(duration, 4),
                    "error": str(e),
                }

    def _execute_in_docker(
        self,
        code_or_project: Union[str, Dict[str, str]],
        entrypoint: str = "main.py",
        manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="codeforge_docker_") as temp_dir:
            temp_path = Path(temp_dir).resolve()
            if isinstance(code_or_project, dict):
                for rel_path, content in code_or_project.items():
                    target = (temp_path / rel_path).resolve()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
            else:
                (temp_path / entrypoint).write_text(str(code_or_project), encoding="utf-8")

            cmd = [
                "docker", "run", "--rm",
                "--network", "none" if not self.allow_network else "bridge",
                "-m", f"{self.memory_limit_mb}m",
                "-v", f"{temp_path}:/app",
                "-w", "/app",
                "python:3.11-slim",
                "python", entrypoint,
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                duration = time.perf_counter() - start_time
                success = (proc.returncode == 0)
                return {
                    "success": success,
                    "output": proc.stdout or "",
                    "stderr": proc.stderr or "",
                    "exit_code": proc.returncode,
                    "duration": round(duration, 4),
                    "error": proc.stderr if not success else None,
                }
            except subprocess.TimeoutExpired:
                duration = time.perf_counter() - start_time
                return {
                    "success": False,
                    "output": "",
                    "stderr": f"Docker container timed out after {self.timeout}s",
                    "exit_code": 124,
                    "duration": round(duration, 4),
                    "error": "Timeout expired",
                }
            except Exception as e:
                duration = time.perf_counter() - start_time
                return {
                    "success": False,
                    "output": "",
                    "stderr": str(e),
                    "exit_code": 1,
                    "duration": round(duration, 4),
                    "error": str(e),
                }

