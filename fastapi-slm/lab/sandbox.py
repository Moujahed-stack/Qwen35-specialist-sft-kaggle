import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

DOCKER_IMAGE = "lab-sandbox"
_warned = False


@dataclass
class RunResult:
    passed: bool
    reason: str        # passed | tests_failed | error | timeout
    seconds: float
    output: str


def _docker_ready() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        r = subprocess.run(["docker", "image", "inspect", DOCKER_IMAGE],
                           capture_output=True, timeout=20)
        return r.returncode == 0
    except Exception:
        return False


def resolve_mode(mode: str) -> str:
    global _warned
    if mode == "auto":
        if _docker_ready():
            return "docker"
        if not _warned:
            print("[sandbox] docker image 'lab-sandbox' not found; using subprocess mode "
                  "(NOT isolated: only run code from models you trust). "
                  "Build the image with: docker build -f Dockerfile.sandbox -t lab-sandbox .")
            _warned = True
        return "subprocess"
    return mode


def _limits(timeout):
    def apply():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (timeout + 5, timeout + 5))
        resource.setrlimit(resource.RLIMIT_FSIZE, (50 * 1024 * 1024, 50 * 1024 * 1024))
    return apply


def _classify(returncode: int) -> str:
    if returncode == 0:
        return "passed"
    if returncode == 1:
        return "tests_failed"
    return "error"          # collection/import error, usage error, no tests, ...


def run_tests(code: str, test_file, timeout: int = 30, mode: str = "auto") -> RunResult:
    mode = resolve_mode(mode)
    start = time.time()
    with tempfile.TemporaryDirectory(prefix="lab_") as tmp_s:
        tmp = Path(tmp_s)
        (tmp / "main.py").write_text(code, encoding="utf-8")
        shutil.copy(str(test_file), str(tmp / "test_task.py"))
        pytest_args = ["-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "test_task.py"]

        if mode == "docker":
            name = f"lab-{uuid.uuid4().hex[:12]}"
            cmd = ["docker", "run", "--rm", "--name", name, "--network", "none",
                   "--memory", "512m", "--cpus", "1", "--pids-limit", "128",
                   "-v", f"{tmp}:/work", "-w", "/work", DOCKER_IMAGE, "python"] + pytest_args
            kwargs = {}
        else:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(tmp),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONIOENCODING": "utf-8",
            }
            if os.name == "nt":
                for k in ("SYSTEMROOT", "TEMP", "TMP"):
                    env[k] = os.environ.get(k, "")
            cmd = [sys.executable] + pytest_args
            kwargs = {"cwd": str(tmp), "env": env}
            if os.name == "posix":
                kwargs["preexec_fn"] = _limits(timeout)

        try:
            p = subprocess.run(cmd, capture_output=True, timeout=timeout, **kwargs)
            out = (p.stdout + p.stderr).decode("utf-8", errors="replace")
            return RunResult(p.returncode == 0, _classify(p.returncode), time.time() - start, out[-3000:])
        except subprocess.TimeoutExpired as e:
            if mode == "docker":
                subprocess.run(["docker", "kill", name], capture_output=True)
            out = ((e.stdout or b"") + (e.stderr or b"")).decode("utf-8", errors="replace")
            return RunResult(False, "timeout", time.time() - start, out[-3000:])
