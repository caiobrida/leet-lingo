import logging
import subprocess
import textwrap
import time

import pytest
from conftest import (
    A_SUBMISSION,
    RETURNS_ITS_ARGUMENT,
    SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
)

from executor import sandbox
from executor.anomalies import OPERATOR_ANOMALIES
from executor.judging import judge
from executor.limits import Limits
from executor.streams import send_and_collect
from executor.submission import TestCase, Verdict

NEVER_RETURNS = textwrap.dedent(
    """
    def solve():
        while True:
            pass
    """
)

NEVER_RETURNS_ON_THE_FIRST_TEST_CASE = textwrap.dedent(
    """
    def solve(number):
        while number == 0:
            pass
        return number
    """
)

SLEEPS_BEFORE_IT_RETURNS = textwrap.dedent(
    """
    import time

    def solve(number):
        time.sleep(1)
        return number
    """
)

FILLS_THE_SANDBOX_WITH_PROCESSES_THEN_NEVER_RETURNS = textwrap.dedent(
    """
    import os
    import time

    def fill_the_sandbox_with_processes():
        while True:
            try:
                if os.fork() == 0:
                    os.setsid()
                    time.sleep(3600)
                    os._exit(0)
            except OSError:
                return

    def solve(number, most_a_single_test_case_needs):
        if number == 0:
            fill_the_sandbox_with_processes()
            while True:
                pass
        running = [entry for entry in os.listdir("/proc") if entry.isdigit()]
        return len(running) <= most_a_single_test_case_needs
    """
)

MOST_PROCESSES_A_SINGLE_TEST_CASE_NEEDS = 8

A_BUDGET_SHORTER_THAN_THE_TEST_CASES_NEED = Limits(test_case_seconds=2.0, submission_seconds=3.0)

SOONER_THAN_A_KILL_FROM_OUTSIDE_COULD_HAVE_DONE_IT = Limits().sandbox_seconds
SECONDS_A_KILL_FROM_OUTSIDE_LEAVES_ROOM_FOR = 20.0

TEST_CASES_THE_SOLUTION_ANSWERS_BEFORE_IT_WEDGES = 2
MORE_TEST_CASES_THAN_A_WEDGED_SUBMISSION_CAN_REACH = 5

WEDGED_TEST_CASES = [
    TestCase(
        input=[number, TEST_CASES_THE_SOLUTION_ANSWERS_BEFORE_IT_WEDGES],
        expected_output=number,
    )
    for number in range(MORE_TEST_CASES_THAN_A_WEDGED_SUBMISSION_CAN_REACH)
]

WHAT_A_WEDGED_SUBMISSION_REPORTS = [
    Verdict.accepted
] * TEST_CASES_THE_SOLUTION_ANSWERS_BEFORE_IT_WEDGES + [Verdict.time_limit_exceeded]

TEST_CASES_ANSWERED_BEFORE_THE_KILL_LANDS = 3
LATE_ENOUGH_TO_FIRE_ONCE_EVERY_RESULT_IS_IN = Limits(sandbox_seconds=3.0)
SECONDS_THE_OUTER_TIMEOUT_IS_OUTLASTED_BY = 5.0


def test_a_solution_that_never_returns_is_stopped_rather_than_left_to_hang() -> None:
    started = time.monotonic()

    judged = judge(
        A_SUBMISSION,
        solution=NEVER_RETURNS,
        test_cases=[TestCase(input=[], expected_output=1)],
    )

    assert time.monotonic() - started < SOONER_THAN_A_KILL_FROM_OUTSIDE_COULD_HAVE_DONE_IT
    assert judged.verdict is Verdict.time_limit_exceeded


def test_a_test_case_cut_off_by_the_timeout_leaves_the_remaining_test_cases_judged() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=NEVER_RETURNS_ON_THE_FIRST_TEST_CASE,
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(3)],
    )

    assert judged.verdict is Verdict.time_limit_exceeded
    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.time_limit_exceeded,
        Verdict.accepted,
        Verdict.accepted,
    ]


def test_nothing_a_timed_out_test_case_started_is_still_running_on_the_next_one() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=FILLS_THE_SANDBOX_WITH_PROCESSES_THEN_NEVER_RETURNS,
        test_cases=[
            TestCase(
                input=[number, MOST_PROCESSES_A_SINGLE_TEST_CASE_NEEDS],
                expected_output=True,
            )
            for number in range(2)
        ],
    )

    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.time_limit_exceeded,
        Verdict.accepted,
    ]


def test_a_submission_exceeding_its_budget_stops_and_keeps_the_results_it_finished() -> None:
    test_cases = [TestCase(input=[number], expected_output=number) for number in range(8)]

    judged = judge(
        A_SUBMISSION,
        solution=SLEEPS_BEFORE_IT_RETURNS,
        test_cases=test_cases,
        limits=A_BUDGET_SHORTER_THAN_THE_TEST_CASES_NEED,
    )

    results = judged.test_case_results
    assert judged.verdict is Verdict.time_limit_exceeded
    assert 1 < len(results) < len(test_cases)
    assert results[-1].verdict is Verdict.time_limit_exceeded
    assert [result.verdict for result in results[:-1]] == [Verdict.accepted] * (len(results) - 1)


def test_a_sandbox_whose_harness_can_no_longer_enforce_anything_is_killed_from_outside() -> None:
    started = time.monotonic()

    judged = judge(
        A_SUBMISSION,
        solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
        test_cases=WEDGED_TEST_CASES,
        limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    )

    assert time.monotonic() - started < SECONDS_A_KILL_FROM_OUTSIDE_LEAVES_ROOM_FOR
    assert judged.verdict is Verdict.time_limit_exceeded


def test_a_submission_killed_from_outside_keeps_the_results_that_finished_before_it() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
        test_cases=WEDGED_TEST_CASES,
        limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    )

    results = judged.test_case_results
    assert len(results) < len(WEDGED_TEST_CASES)
    assert [result.verdict for result in results] == WHAT_A_WEDGED_SUBMISSION_REPORTS


def test_a_sandbox_killed_from_outside_after_every_result_keeps_the_verdict_it_earned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sandbox, "send_and_collect", _collect_everything_then_outlast_the_timeout)

    judged = judge(
        A_SUBMISSION,
        solution=RETURNS_ITS_ARGUMENT,
        test_cases=[
            TestCase(input=[number], expected_output=number)
            for number in range(TEST_CASES_ANSWERED_BEFORE_THE_KILL_LANDS)
        ],
        limits=LATE_ENOUGH_TO_FIRE_ONCE_EVERY_RESULT_IS_IN,
    )

    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.accepted
    ] * TEST_CASES_ANSWERED_BEFORE_THE_KILL_LANDS
    assert judged.verdict is Verdict.accepted


def _collect_everything_then_outlast_the_timeout(
    process: "subprocess.Popen[str]",
    document: str,
) -> str:
    collected = send_and_collect(process, document)
    time.sleep(SECONDS_THE_OUTER_TIMEOUT_IS_OUTLASTED_BY)
    return collected


def test_a_sandbox_killed_from_outside_is_recorded_as_an_operator_anomaly(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        judge(
            A_SUBMISSION,
            solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
            test_cases=WEDGED_TEST_CASES,
            limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
        )

    assert [record.name for record in caplog.records] == [OPERATOR_ANOMALIES.name]


def test_the_outer_timeout_firing_never_appears_in_what_the_learner_is_shown(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        judged = judge(
            A_SUBMISSION,
            solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
            test_cases=WEDGED_TEST_CASES,
            limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
        )

    killed_on = judged.test_case_results[-1]
    assert caplog.records != []
    assert judged.verdict is Verdict.time_limit_exceeded
    assert killed_on.verdict is Verdict.time_limit_exceeded
    assert all(result.error is None for result in judged.test_case_results)
    assert all(result.printed_output == "" for result in judged.test_case_results)
