import subprocess

from executor.limits import Limits
from executor.streams import send_and_collect

SANDBOX_IMAGE = "leet-lingo-sandbox:latest"

CUT_OFF_FROM_EVERYTHING_OUTSIDE_THE_SANDBOX = [
    "--network=none",
    "--read-only",
    "--tmpfs=/dev/shm:mode=0555",
]

NO_PRIVILEGE_BEYOND_ASSIGNING_THE_SOLUTION_ITS_OWN_USER = [
    "--cap-drop=ALL",
    "--cap-add=SETUID",
    "--cap-add=SETGID",
    "--security-opt=no-new-privileges",
]


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
        *CUT_OFF_FROM_EVERYTHING_OUTSIDE_THE_SANDBOX,
        *NO_PRIVILEGE_BEYOND_ASSIGNING_THE_SOLUTION_ITS_OWN_USER,
        *_capped_at(limits),
        SANDBOX_IMAGE,
    ]


def _capped_at(limits: Limits) -> list[str]:
    return [
        f"--memory={limits.memory_bytes}b",
        f"--memory-swap={limits.memory_bytes}b",
        f"--cpus={limits.cpus}",
        f"--pids-limit={limits.processes}",
    ]
