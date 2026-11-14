"""Policy layer: loads policy.yaml and checks tool calls against the rules."""
from pathlib import Path

import yaml

POLICY_PATH = Path(__file__).parent / "policy.yaml"


def load_policy(path: Path = POLICY_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


POLICY = load_policy()


def check_tool_allowed(tool_name: str):
    """Return (True, "ok") if the tool is allowed, else (False, reason)."""
    if tool_name not in POLICY["allowed_tools"]:
        return False, f"tool '{tool_name}' is not in allowed_tools"
    return True, "ok"


def check_code(code: str):
    """Return (True, "ok") if the code passes the rules, else (False, reason)."""
    if len(code) > POLICY["max_code_length"]:
        return False, "code is longer than max_code_length"
    lowered = code.lower()
    for pattern in POLICY["blocked_code_patterns"]:
        if pattern.lower() in lowered:
            return False, f"code contains blocked pattern '{pattern}'"
    return True, "ok"
