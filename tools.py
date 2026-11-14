"""Tools the agent can use. EVERY call goes through guarded_call():
policy check -> run -> log.
"""
import time
from pathlib import Path

from logger import log_action
from policy import POLICY, check_code, check_tool_allowed
from sandbox import run_in_sandbox

PROJECT_DIR = Path(__file__).parent
WORKSPACE = (PROJECT_DIR / POLICY["workspace_folder"]).resolve()


def _blocked(reason: str) -> dict:
    return {"status": "blocked_policy", "reason": reason, "output": f"BLOCKED: {reason}"}


# ---------- real implementations ----------

def _read_file_impl(path: str) -> dict:
    # Reject absolute paths and drive letters outright (C:\..., /etc/..., \\server\...)
    if Path(path).is_absolute() or ":" in path or path.startswith(("/", "\\")):
        return _blocked(f"absolute path '{path}' is not allowed")
    # Resolve the real location (follows .. and shortcuts) and make sure it's inside the workspace
    target = (WORKSPACE / path).resolve()
    if not target.is_relative_to(WORKSPACE):
        return _blocked(f"path '{path}' is outside the workspace folder")
    if not target.is_file():
        return {"status": "error", "reason": "file not found", "output": f"File not found: {path}"}
    text = target.read_text(encoding="utf-8", errors="replace")
    return {"status": "ok", "reason": "ok", "output": text[: POLICY["sandbox"]["max_output_chars"]]}


def _run_python_impl(code: str) -> dict:
    ok, reason = check_code(code)
    if not ok:
        return _blocked(reason)
    result = run_in_sandbox(code)
    return {"status": result["status"], "reason": result["status"], "output": result["output"]}


IMPLEMENTATIONS = {
    "run_python": _run_python_impl,
    "read_file": _read_file_impl,
}


# ---------- the guard ----------

def guarded_call(tool_name: str, args: dict) -> dict:
    """Check the policy, run the tool, and log the result."""
    start = time.perf_counter()
    ok, reason = check_tool_allowed(tool_name)
    if not ok:
        result = _blocked(reason)
    elif tool_name not in IMPLEMENTATIONS:
        result = _blocked(f"tool '{tool_name}' has no implementation")
    else:
        try:
            result = IMPLEMENTATIONS[tool_name](**args)
        except TypeError as e:
            result = {"status": "error", "reason": f"bad arguments: {e}", "output": f"Bad arguments: {e}"}
    duration_ms = (time.perf_counter() - start) * 1000
    log_action(tool_name, args, result, duration_ms)
    return result


# ---------- what the AI model sees ----------
# Ollama reads these function names, type hints and docstrings
# to tell the model which tools exist.

def run_python(code: str) -> str:
    """Run Python code in a secure sandbox and return what it prints.

    Args:
        code: The Python code to run. Use print() to show results.
    """
    return guarded_call("run_python", {"code": code})["output"]


def read_file(path: str) -> str:
    """Read a text file from the workspace folder.

    Args:
        path: The file name inside the workspace folder, for example notes.txt
    """
    return guarded_call("read_file", {"path": path})["output"]
