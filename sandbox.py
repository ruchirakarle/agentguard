"""Sandbox layer: runs untrusted Python code inside a locked-down Docker container."""
from typing import Optional

import docker

from policy import POLICY

_client = None


def get_client():
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def ensure_image(image: str) -> None:
    """Download the container image the first time we need it."""
    client = get_client()
    try:
        client.images.get(image)
    except docker.errors.ImageNotFound:
        print(f"Downloading {image} (first time only, may take a minute)...")
        client.images.pull(image)


def run_in_sandbox(code: str, timeout: Optional[int] = None) -> dict:
    """Run code in an isolated container and return a result dict.

    status is one of: ok, error, blocked_timeout, blocked_memory
    """
    cfg = POLICY["sandbox"]
    timeout = timeout or cfg["timeout_seconds"]
    max_chars = cfg["max_output_chars"]
    ensure_image(cfg["image"])

    container = get_client().containers.run(
        cfg["image"],
        ["python", "-c", code],
        detach=True,
        network_disabled=True,                          # no internet
        mem_limit=cfg["memory_limit"],                  # RAM cap
        memswap_limit=cfg["memory_limit"],              # no extra swap
        nano_cpus=int(cfg["cpu_limit"] * 1_000_000_000),  # CPU cap
        pids_limit=cfg["max_processes"],                # process/thread cap
        read_only=True,                                 # can't write files
        cap_drop=["ALL"],                               # drop Linux privileges
        security_opt=["no-new-privileges"],
        user="nobody",                                  # not root
    )

    try:
        try:
            result = container.wait(timeout=timeout)
        except Exception:
            try:
                container.kill()
            except Exception:
                pass
            return {
                "status": "blocked_timeout",
                "exit_code": None,
                "output": f"Stopped: code ran longer than {timeout}s",
            }

        container.reload()
        exit_code = result.get("StatusCode")
        if container.attrs["State"].get("OOMKilled") or exit_code == 137:
            return {
                "status": "blocked_memory",
                "exit_code": exit_code,
                "output": "Stopped: memory limit exceeded",
            }

        output = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
        if len(output) > max_chars:
            output = output[:max_chars] + "\n...[output truncated]"

        return {
            "status": "ok" if exit_code == 0 else "error",
            "exit_code": exit_code,
            "output": output,
        }
    finally:
        container.remove(force=True)
