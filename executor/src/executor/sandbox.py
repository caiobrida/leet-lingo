import subprocess

from executor.limits import Limits
from executor.streams import send_and_collect

SANDBOX_IMAGE = "leet-lingo-sandbox:latest"


def run_sandbox(payload: str, limits: Limits) -> str:
    sandbox = subprocess.Popen(
        _docker_run_command(limits),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    )
    emitted = send_and_collect(sandbox, payload)
    sandbox.wait()
    return emitted


def _docker_run_command(limits: Limits) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--interactive",
        f"--memory={limits.memory_bytes}b",
        f"--memory-swap={limits.memory_bytes}b",
        f"--cpus={limits.cpus}",
        f"--pids-limit={limits.processes}",
        SANDBOX_IMAGE,
    ]
