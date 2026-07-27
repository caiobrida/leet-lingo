import argparse
import json
import shlex
import subprocess
import sys
from collections.abc import Sequence
from typing import IO

from executor.limits import Limits
from executor.sandbox import the_command_a_document_is_piped_into, the_document_a_sandbox_receives
from executor.submission import TestCase

THE_COMMAND_AN_OPERATOR_RUNS = "python -m executor.replay"

WHAT_A_REPLAY_IS_FOR = (
    "Judge one submission again in a sandbox configured the way the executor configured it, "
    "from the solution and test cases a report carries and the limits its log lines named."
)

NOTHING_A_TEST_CASE_CAN_BE_READ_FROM = (
    "carries no list of test cases, each an input and an expected output"
)

A_FILE_AN_OPERATOR_POINTS_AT = argparse.FileType("r", encoding="utf-8")


def main(arguments: Sequence[str] | None = None) -> int:
    asking = _the_arguments_a_replay_takes()
    asked_for = asking.parse_args(arguments)
    limits = Limits(
        test_case_seconds=asked_for.test_case_seconds,
        submission_seconds=asked_for.submission_seconds,
        memory_bytes=asked_for.memory_bytes,
        cpus=asked_for.cpus,
        processes=asked_for.processes,
    )
    try:
        test_cases = _the_test_cases_in(asked_for.test_cases)
    except (LookupError, TypeError, ValueError):
        asking.error(f"{asked_for.test_cases.name} {NOTHING_A_TEST_CASE_CAN_BE_READ_FROM}")
    document = the_document_a_sandbox_receives(asked_for.solution.read(), test_cases, limits)
    command = the_command_a_document_is_piped_into(limits)
    print(shlex.join(command), file=sys.stderr)
    if asked_for.document:
        sys.stdout.write(document)
        return 0
    return subprocess.run(command, input=document, text=True).returncode


def _the_arguments_a_replay_takes() -> argparse.ArgumentParser:
    asking = argparse.ArgumentParser(
        prog=THE_COMMAND_AN_OPERATOR_RUNS,
        description=WHAT_A_REPLAY_IS_FOR,
    )
    unless_overridden = Limits()
    asking.add_argument("solution", type=A_FILE_AN_OPERATOR_POINTS_AT)
    asking.add_argument("test_cases", type=A_FILE_AN_OPERATOR_POINTS_AT)
    asking.add_argument(
        "--test-case-seconds",
        type=float,
        default=unless_overridden.test_case_seconds,
    )
    asking.add_argument(
        "--submission-seconds",
        type=float,
        default=unless_overridden.submission_seconds,
    )
    asking.add_argument("--memory-bytes", type=int, default=unless_overridden.memory_bytes)
    asking.add_argument("--cpus", type=float, default=unless_overridden.cpus)
    asking.add_argument("--processes", type=int, default=unless_overridden.processes)
    asking.add_argument("--document", action="store_true")
    return asking


def _the_test_cases_in(catalogued: IO[str]) -> list[TestCase]:
    return [
        TestCase(input=entry["input"], expected_output=entry["expected_output"])
        for entry in json.load(catalogued)
    ]


if __name__ == "__main__":
    raise SystemExit(main())
