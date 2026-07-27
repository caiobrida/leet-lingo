import json
import logging
import shlex
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
from conftest import (
    A_SUBMISSION,
    RETURNS_ITS_ARGUMENT,
    SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
    containers_still_on_the_host,
)

from executor import sandbox
from executor.judging import judge
from executor.limits import Limits
from executor.logs import the_executors_log_format
from executor.replay import THE_STATUS_A_REPLAY_KILLED_FROM_OUTSIDE_LEAVES
from executor.results import read_test_case_results
from executor.sandbox import (
    SANDBOX_IMAGE,
    the_command_a_document_is_piped_into,
    the_document_a_sandbox_receives,
)
from executor.streams import send_and_collect
from executor.submission import TestCase, Verdict

THREE_TEST_CASES = [TestCase(input=[number], expected_output=number) for number in range(3)]

LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER = Limits(
    test_case_seconds=1.5,
    submission_seconds=7.0,
    sandbox_seconds=11.0,
    memory_bytes=200 * 1024 * 1024,
    cpus=0.5,
    processes=32,
)

THE_LIMITS_THAT_SHAPE_THE_SANDBOX = {
    "--memory=209715200b",
    "--memory-swap=209715200b",
    "--cpus=0.5",
    "--pids-limit=32",
}

THE_PROTECTIONS_A_REPLAY_RUNS_UNDER_TOO = {
    "--network=none",
    "--read-only",
    "--cap-drop=ALL",
    "--security-opt=no-new-privileges",
}

EVERY_LIMIT_AN_OPERATOR_READS_OFF_THE_LOGS = {
    "test_case_seconds=1.5",
    "submission_seconds=7.0",
    "sandbox_seconds=11.0",
    "memory_bytes=209715200",
    "cpus=0.5",
    "processes=32",
}

HOW_MANY_TEST_CASES_THE_SUBMISSION_HAD = "3 test cases"

WEDGES_ON_ITS_ONLY_TEST_CASE = 0
SECONDS_FOR_A_KILLED_CONTAINER_TO_LEAVE_THE_HOST = 15.0

A_SUBMISSION_REPLAYED_FROM_WHAT_ITS_LOG_LINES_RECORD = "submission-replayed-from-its-log-lines"

AN_EXPECTED_OUTPUT_NOTHING_MAY_RETAIN = "the-expected-output-nothing-may-retain"
A_SOLUTION_NOTHING_MAY_RETAIN = textwrap.dedent(
    f"""
    def solve(number):
        return "{AN_EXPECTED_OUTPUT_NOTHING_MAY_RETAIN}"
    """
)

IS_WRONG_ON_ONE_TEST_CASE_AND_PRINTS_ON_EVERY_ONE = textwrap.dedent(
    """
    def solve(number):
        print("looking at", number)
        if number == 1:
            return number + 1
        return number
    """
)


def _the_flags_the_logs_would_have_named(limits: Limits) -> list[str]:
    return [
        "--test-case-seconds",
        str(limits.test_case_seconds),
        "--submission-seconds",
        str(limits.submission_seconds),
        "--sandbox-seconds",
        str(limits.sandbox_seconds),
        "--memory-bytes",
        str(limits.memory_bytes),
        "--cpus",
        str(limits.cpus),
        "--processes",
        str(limits.processes),
    ]


def _the_host_once_a_killed_replay_has_left_it() -> list[str]:
    give_up_at = time.monotonic() + SECONDS_FOR_A_KILLED_CONTAINER_TO_LEAVE_THE_HOST
    still_on_the_host = containers_still_on_the_host()
    while still_on_the_host != [] and time.monotonic() < give_up_at:
        still_on_the_host = containers_still_on_the_host()
    return still_on_the_host


def _a_replay_an_operator_runs(
    tmp_path: Path,
    solution: str,
    test_cases: list[TestCase],
    limits: Limits,
    *asked_for: str,
) -> "subprocess.CompletedProcess[str]":
    reported_solution = tmp_path / "solution.py"
    reported_solution.write_text(solution)
    catalogued_test_cases = tmp_path / "test_cases.json"
    catalogued_test_cases.write_text(
        json.dumps(
            [
                {"input": test_case.input, "expected_output": test_case.expected_output}
                for test_case in test_cases
            ]
        )
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "executor.replay",
            str(reported_solution),
            str(catalogued_test_cases),
            *_the_flags_the_logs_would_have_named(limits),
            *asked_for,
        ],
        capture_output=True,
        text=True,
    )


def test_the_document_a_sandbox_receives_can_be_obtained_without_judging_the_submission() -> None:
    still_on_the_host = containers_still_on_the_host()

    document = the_document_a_sandbox_receives(
        RETURNS_ITS_ARGUMENT,
        THREE_TEST_CASES,
        LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
    )

    assert json.loads(document) == {
        "solution": RETURNS_ITS_ARGUMENT,
        "test_cases": [
            {"input": [0], "expected_output": 0},
            {"input": [1], "expected_output": 1},
            {"input": [2], "expected_output": 2},
        ],
        "limits": {"test_case_seconds": 1.5, "submission_seconds": 7.0},
    }
    assert containers_still_on_the_host() == still_on_the_host


def test_the_command_an_operator_is_given_carries_the_limits_the_submission_ran_under() -> None:
    command = the_command_a_document_is_piped_into(LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER)

    assert command[:4] == ["docker", "run", "--rm", "--interactive"]
    assert command[-1] == SANDBOX_IMAGE
    assert THE_LIMITS_THAT_SHAPE_THE_SANDBOX <= set(command)
    assert THE_PROTECTIONS_A_REPLAY_RUNS_UNDER_TOO <= set(command)


def test_the_document_obtained_without_judging_is_the_one_judging_sends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []

    def keep_what_the_sandbox_was_sent(process: "subprocess.Popen[str]", document: str) -> str:
        sent.append(document)
        return send_and_collect(process, document)

    monkeypatch.setattr(sandbox, "send_and_collect", keep_what_the_sandbox_was_sent)

    judge(
        A_SUBMISSION,
        solution=RETURNS_ITS_ARGUMENT,
        test_cases=THREE_TEST_CASES,
        limits=LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
    )

    assert sent == [
        the_document_a_sandbox_receives(
            RETURNS_ITS_ARGUMENT,
            THREE_TEST_CASES,
            LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
        )
    ]


def test_a_replay_an_operator_runs_reproduces_the_submission_that_was_reported(
    tmp_path: Path,
) -> None:
    judged = judge(
        A_SUBMISSION,
        solution=IS_WRONG_ON_ONE_TEST_CASE_AND_PRINTS_ON_EVERY_ONE,
        test_cases=THREE_TEST_CASES,
        limits=LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
    )

    replayed = _a_replay_an_operator_runs(
        tmp_path,
        IS_WRONG_ON_ONE_TEST_CASE_AND_PRINTS_ON_EVERY_ONE,
        THREE_TEST_CASES,
        LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
    )

    assert judged.verdict is Verdict.wrong_answer
    assert replayed.returncode == 0
    assert read_test_case_results(replayed.stdout, THREE_TEST_CASES) == judged.test_case_results


def test_a_replay_of_a_submission_that_never_stops_is_killed_from_outside(tmp_path: Path) -> None:
    replayed = _a_replay_an_operator_runs(
        tmp_path,
        WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
        [TestCase(input=[0, WEDGES_ON_ITS_ONLY_TEST_CASE], expected_output=0)],
        SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    )

    assert replayed.returncode == THE_STATUS_A_REPLAY_KILLED_FROM_OUTSIDE_LEAVES
    assert _the_host_once_a_killed_replay_has_left_it() == []


def test_the_document_and_the_command_an_operator_is_given_reproduce_the_submission_by_hand(
    tmp_path: Path,
) -> None:
    judged = judge(
        A_SUBMISSION,
        solution=IS_WRONG_ON_ONE_TEST_CASE_AND_PRINTS_ON_EVERY_ONE,
        test_cases=THREE_TEST_CASES,
        limits=LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
    )

    handed_over = _a_replay_an_operator_runs(
        tmp_path,
        IS_WRONG_ON_ONE_TEST_CASE_AND_PRINTS_ON_EVERY_ONE,
        THREE_TEST_CASES,
        LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
        "--document",
    )
    piped_in_by_hand = subprocess.run(
        shlex.split(handed_over.stderr),
        input=handed_over.stdout,
        capture_output=True,
        text=True,
        check=True,
    )

    assert read_test_case_results(piped_in_by_hand.stdout, THREE_TEST_CASES) == (
        judged.test_case_results
    )


def test_the_limits_and_the_test_case_count_a_submission_ran_under_are_logged_with_it(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        judge(
            A_SUBMISSION_REPLAYED_FROM_WHAT_ITS_LOG_LINES_RECORD,
            solution=RETURNS_ITS_ARGUMENT,
            test_cases=THREE_TEST_CASES,
            limits=LIMITS_A_SUBMISSION_IS_REPLAYED_UNDER,
        )

    lines = [the_executors_log_format().format(record) for record in caplog.records]

    assert [
        line
        for line in lines
        if A_SUBMISSION_REPLAYED_FROM_WHAT_ITS_LOG_LINES_RECORD in line
        and HOW_MANY_TEST_CASES_THE_SUBMISSION_HAD in line
        and EVERY_LIMIT_AN_OPERATOR_READS_OFF_THE_LOGS <= set(line.split())
    ] != []


def test_neither_the_solution_nor_the_expected_outputs_reach_a_log_line(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        judged = judge(
            A_SUBMISSION,
            solution=A_SOLUTION_NOTHING_MAY_RETAIN,
            test_cases=[
                TestCase(input=[0], expected_output=AN_EXPECTED_OUTPUT_NOTHING_MAY_RETAIN)
            ],
        )

    lines = [the_executors_log_format().format(record) for record in caplog.records]

    assert judged.verdict is Verdict.accepted
    assert lines != []
    assert [
        line
        for line in lines
        if AN_EXPECTED_OUTPUT_NOTHING_MAY_RETAIN in line or "def solve" in line
    ] == []


def test_judging_a_submission_writes_nothing_to_disk(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    judge(
        A_SUBMISSION,
        solution=A_SOLUTION_NOTHING_MAY_RETAIN,
        test_cases=[TestCase(input=[0], expected_output=AN_EXPECTED_OUTPUT_NOTHING_MAY_RETAIN)],
    )

    assert list(tmp_path.iterdir()) == []
