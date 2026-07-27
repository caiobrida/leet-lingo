import argparse
import json
import shlex
import subprocess
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path

from executor.limits import Limits
from executor.sandbox import (
    A_NAME_ONLY_OUR_CONTAINERS_CARRY,
    kill_the_container,
    the_command_a_document_is_piped_into,
    the_document_a_sandbox_receives,
)
from executor.submission import TestCase

THE_COMMAND_AN_OPERATOR_RUNS = "python -m executor.replay"

WHAT_A_REPLAY_IS_FOR = (
    "Judge one submission again in a sandbox configured the way the executor configured it, "
    "from the solution and test cases a report carries and the limits its log lines named. "
    "The document the sandbox receives is written to stdout by --document, and the docker run "
    "invocation it is piped into is written to stderr either way."
)

WHAT_A_SOLUTION_IS_READ_FROM = "file holding the solution, defining solve"

WHAT_TEST_CASES_ARE_READ_FROM = (
    'JSON file holding a list of {"input": [...], "expected_output": ...}'
)

WHAT_A_DOCUMENT_IS_ASKED_FOR_INSTEAD_OF = (
    "write the document to stdout instead of piping it into a sandbox"
)

NOT_A_LIST_OF_TEST_CASES = "carries no list of test cases, each an input and an expected output"

THE_STATUS_A_REPLAY_KILLED_FROM_OUTSIDE_LEAVES = 124


def main(arguments: Sequence[str] | None = None) -> int:
    what_a_replay_takes = _the_arguments_a_replay_takes()
    asked_for = what_a_replay_takes.parse_args(arguments)
    limits = Limits(
        test_case_seconds=asked_for.test_case_seconds,
        submission_seconds=asked_for.submission_seconds,
        sandbox_seconds=asked_for.sandbox_seconds,
        memory_bytes=asked_for.memory_bytes,
        cpus=asked_for.cpus,
        processes=asked_for.processes,
    )
    try:
        solution = asked_for.solution.read_text(encoding="utf-8")
        test_cases = _the_test_cases_in(asked_for.test_cases)
    except OSError as unreadable:
        what_a_replay_takes.error(str(unreadable))
    except (LookupError, TypeError, ValueError):
        what_a_replay_takes.error(f"{asked_for.test_cases} {NOT_A_LIST_OF_TEST_CASES}")
    document = the_document_a_sandbox_receives(solution, test_cases, limits)
    container = _a_name_for_one_replay()
    command = the_command_a_document_is_piped_into(limits, f"--name={container}")
    print(shlex.join(command), file=sys.stderr)
    if asked_for.document:
        sys.stdout.write(document)
        return 0
    return _pipe_the_document_in_until_the_sandbox_stops(
        command,
        document,
        container,
        limits.sandbox_seconds,
    )


def _pipe_the_document_in_until_the_sandbox_stops(
    command: list[str],
    document: str,
    container: str,
    sandbox_seconds: float,
) -> int:
    try:
        replayed = subprocess.run(command, input=document, text=True, timeout=sandbox_seconds)
    except subprocess.TimeoutExpired:
        kill_the_container(container)
        return THE_STATUS_A_REPLAY_KILLED_FROM_OUTSIDE_LEAVES
    return replayed.returncode


def _the_arguments_a_replay_takes() -> argparse.ArgumentParser:
    what_a_replay_takes = argparse.ArgumentParser(
        prog=THE_COMMAND_AN_OPERATOR_RUNS,
        description=WHAT_A_REPLAY_IS_FOR,
    )
    unless_overridden = Limits()
    what_a_replay_takes.add_argument("solution", type=Path, help=WHAT_A_SOLUTION_IS_READ_FROM)
    what_a_replay_takes.add_argument("test_cases", type=Path, help=WHAT_TEST_CASES_ARE_READ_FROM)
    for limit, bound in (
        ("--test-case-seconds", unless_overridden.test_case_seconds),
        ("--submission-seconds", unless_overridden.submission_seconds),
        ("--sandbox-seconds", unless_overridden.sandbox_seconds),
        ("--cpus", unless_overridden.cpus),
    ):
        what_a_replay_takes.add_argument(limit, type=float, default=bound)
    for limit, counted in (
        ("--memory-bytes", unless_overridden.memory_bytes),
        ("--processes", unless_overridden.processes),
    ):
        what_a_replay_takes.add_argument(limit, type=int, default=counted)
    what_a_replay_takes.add_argument(
        "--document",
        action="store_true",
        help=WHAT_A_DOCUMENT_IS_ASKED_FOR_INSTEAD_OF,
    )
    return what_a_replay_takes


def _the_test_cases_in(catalogued_test_cases: Path) -> list[TestCase]:
    return [
        TestCase(input=entry["input"], expected_output=entry["expected_output"])
        for entry in json.loads(catalogued_test_cases.read_text(encoding="utf-8"))
    ]


def _a_name_for_one_replay() -> str:
    return f"{A_NAME_ONLY_OUR_CONTAINERS_CARRY}replay-{uuid.uuid4().hex}"


if __name__ == "__main__":
    raise SystemExit(main())
