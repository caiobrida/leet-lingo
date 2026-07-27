import json
import subprocess
import threading
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from executor.anomalies import record_a_sandbox_killed_from_outside
from executor.limits import Limits
from executor.logs import carrying_the_submission_into_another_thread
from executor.streams import send_and_collect
from executor.submission import TestCase

SANDBOX_IMAGE = "leet-lingo-sandbox:latest"

A_NAME_ONLY_OUR_CONTAINERS_CARRY = "leet-lingo-"

THE_SUBMISSION_A_CONTAINER_CARRIES = "leet-lingo.submission"

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


EMITTED_BY_A_SANDBOX_THAT_NEVER_STARTED = EmittedByTheSandbox(stream="", killed_from_outside=False)


def the_document_a_sandbox_receives(
    solution: str,
    test_cases: Sequence[TestCase],
    limits: Limits,
) -> str:
    return json.dumps(
        {
            "solution": solution,
            "test_cases": [
                {"input": test_case.input, "expected_output": test_case.expected_output}
                for test_case in test_cases
            ],
            "limits": {
                "test_case_seconds": limits.test_case_seconds,
                "submission_seconds": limits.submission_seconds,
            },
        }
    )


def kill_the_container(container: str) -> None:
    try:
        subprocess.run(["docker", "kill", container], capture_output=True)
    except OSError:
        pass


def the_command_a_document_is_piped_into(limits: Limits, *traced_as: str) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--interactive",
        *traced_as,
        *NOTHING_TO_REACH_OUTSIDE_THE_SANDBOX,
        *NOTHING_WRITABLE_INSIDE_THE_SANDBOX,
        *NO_PRIVILEGE_BEYOND_GIVING_THE_SOLUTION_A_USER_AND_KILLING_IT,
        f"--memory={limits.memory_bytes}b",
        f"--memory-swap={limits.memory_bytes}b",
        f"--cpus={limits.cpus}",
        f"--pids-limit={limits.processes}",
        SANDBOX_IMAGE,
    ]


def run_sandbox(submission_id: str, document: str, limits: Limits) -> EmittedByTheSandbox:
    container = _a_name_for_one_container()
    sandbox = _start_the_sandbox(submission_id, container, limits)
    if sandbox is None:
        return EMITTED_BY_A_SANDBOX_THAT_NEVER_STARTED
    try:
        return _collect_until_the_sandbox_stops(sandbox, container, document, limits)
    except BaseException:
        kill_the_container(container)
        sandbox.wait()
        raise


def _collect_until_the_sandbox_stops(
    sandbox: "subprocess.Popen[str]",
    container: str,
    document: str,
    limits: Limits,
) -> EmittedByTheSandbox:
    killed_from_outside = threading.Event()
    killing = threading.Timer(
        limits.sandbox_seconds,
        carrying_the_submission_into_another_thread(_kill_the_container_from_outside),
        args=(container, killed_from_outside),
    )
    killing.start()
    try:
        collected = send_and_collect(sandbox, document)
        sandbox.wait()
    finally:
        killing.cancel()
        killing.join()
    return EmittedByTheSandbox(
        stream=collected,
        killed_from_outside=killed_from_outside.is_set(),
    )


def _start_the_sandbox(
    submission_id: str,
    container: str,
    limits: Limits,
) -> "subprocess.Popen[str] | None":
    try:
        return subprocess.Popen(
            the_command_a_document_is_piped_into(
                limits,
                f"--name={container}",
                f"--label={THE_SUBMISSION_A_CONTAINER_CARRIES}={submission_id}",
            ),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
    except OSError:
        return None


def _kill_the_container_from_outside(
    container: str,
    killed_from_outside: threading.Event,
) -> None:
    killed_from_outside.set()
    record_a_sandbox_killed_from_outside(container)
    kill_the_container(container)


def _a_name_for_one_container() -> str:
    return f"{A_NAME_ONLY_OUR_CONTAINERS_CARRY}{uuid.uuid4().hex}"
