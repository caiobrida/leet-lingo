import subprocess
import threading
import uuid
from dataclasses import dataclass

from executor.anomalies import record_a_sandbox_killed_from_outside
from executor.limits import Limits
from executor.streams import send_and_collect

SANDBOX_IMAGE = "leet-lingo-sandbox:latest"

NOTHING_TO_REACH_OUTSIDE_THE_SANDBOX = [
    "--network=none",
]

NOTHING_WRITABLE_INSIDE_THE_SANDBOX = [
    "--read-only",
    "--tmpfs=/dev/shm:mode=0555",
]

NO_PRIVILEGE_BEYOND_GIVING_THE_SOLUTION_A_USER_AND_KILLING_IT = [
    "--cap-drop=ALL",
    "--cap-add=SETUID",
    "--cap-add=SETGID",
    "--cap-add=KILL",
    "--security-opt=no-new-privileges",
]


@dataclass(frozen=True)
class EmittedByTheSandbox:
    stream: str
    killed_from_outside: bool


def run_sandbox(payload: str, limits: Limits) -> EmittedByTheSandbox:
    container = _a_name_for_one_container()
    sandbox = subprocess.Popen(
        _docker_run_command(container, limits),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    )
    killed_from_outside = threading.Event()
    killing = threading.Timer(
        limits.sandbox_seconds,
        _kill_the_container,
        args=(container, killed_from_outside),
    )
    killing.start()
    try:
        collected = send_and_collect(sandbox, payload)
        sandbox.wait()
    finally:
        killing.cancel()
        killing.join()
    if killed_from_outside.is_set():
        record_a_sandbox_killed_from_outside(container)
    return EmittedByTheSandbox(
        stream=collected,
        killed_from_outside=killed_from_outside.is_set(),
    )


def _kill_the_container(container: str, killed_from_outside: threading.Event) -> None:
    killed = subprocess.run(["docker", "kill", container], capture_output=True)
    if killed.returncode == 0:
        killed_from_outside.set()


def _a_name_for_one_container() -> str:
    return f"leet-lingo-{uuid.uuid4().hex}"


def _docker_run_command(container: str, limits: Limits) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--interactive",
        f"--name={container}",
        *NOTHING_TO_REACH_OUTSIDE_THE_SANDBOX,
        *NOTHING_WRITABLE_INSIDE_THE_SANDBOX,
        *NO_PRIVILEGE_BEYOND_GIVING_THE_SOLUTION_A_USER_AND_KILLING_IT,
        f"--memory={limits.memory_bytes}b",
        f"--memory-swap={limits.memory_bytes}b",
        f"--cpus={limits.cpus}",
        f"--pids-limit={limits.processes}",
        SANDBOX_IMAGE,
    ]
