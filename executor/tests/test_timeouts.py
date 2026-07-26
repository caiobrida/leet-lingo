import logging
import textwrap
import time

import pytest

from executor.anomalies import OPERATOR_ANOMALIES
from executor.judging import judge
from executor.limits import Limits
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

LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT = Limits(
    test_case_seconds=120.0,
    submission_seconds=120.0,
    sandbox_seconds=3.0,
)

SECONDS_A_KILL_FROM_OUTSIDE_LEAVES_ROOM_FOR = 20.0

SOONER_THAN_A_KILL_FROM_OUTSIDE_COULD_HAVE_DONE_IT = Limits().sandbox_seconds

MORE_TEST_CASES_THAN_A_KILLED_SUBMISSION_CAN_REACH = 5


def test_a_solution_that_never_returns_is_stopped_rather_than_left_to_hang() -> None:
    started = time.monotonic()

    judged = judge(
        solution=NEVER_RETURNS,
        test_cases=[TestCase(input=[], expected_output=1)],
    )

    assert time.monotonic() - started < SOONER_THAN_A_KILL_FROM_OUTSIDE_COULD_HAVE_DONE_IT
    assert judged.verdict is Verdict.time_limit_exceeded


def test_a_test_case_cut_off_by_the_timeout_leaves_the_remaining_test_cases_judged() -> None:
    judged = judge(
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
        solution=SLEEPS_BEFORE_IT_RETURNS,
        test_cases=test_cases,
        limits=A_BUDGET_SHORTER_THAN_THE_TEST_CASES_NEED,
    )

    results = judged.test_case_results
    assert judged.verdict is Verdict.time_limit_exceeded
    assert len(results) < len(test_cases)
    assert results[-1].verdict is Verdict.time_limit_exceeded
    assert [result.verdict for result in results[:-1]] == [Verdict.accepted] * (len(results) - 1)
    assert len(results) > 1


def test_a_sandbox_the_harness_cannot_stop_is_killed_from_outside_the_container() -> None:
    started = time.monotonic()

    judged = judge(
        solution=NEVER_RETURNS,
        test_cases=[TestCase(input=[], expected_output=1)],
        limits=LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT,
    )

    assert time.monotonic() - started < SECONDS_A_KILL_FROM_OUTSIDE_LEAVES_ROOM_FOR
    assert judged.verdict is Verdict.time_limit_exceeded


def test_a_submission_killed_from_outside_reports_fewer_results_than_it_has_test_cases() -> None:
    test_cases = [
        TestCase(input=[number], expected_output=number)
        for number in range(MORE_TEST_CASES_THAN_A_KILLED_SUBMISSION_CAN_REACH)
    ]

    judged = judge(
        solution=NEVER_RETURNS_ON_THE_FIRST_TEST_CASE,
        test_cases=test_cases,
        limits=LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT,
    )

    assert judged.verdict is Verdict.time_limit_exceeded
    assert len(judged.test_case_results) < len(test_cases)


def test_a_sandbox_killed_from_outside_is_recorded_as_an_operator_anomaly(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        judge(
            solution=NEVER_RETURNS,
            test_cases=[TestCase(input=[], expected_output=1)],
            limits=LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT,
        )

    assert [record.name for record in caplog.records] == [OPERATOR_ANOMALIES.name]


def test_the_outer_timeout_firing_never_appears_in_what_the_learner_is_shown(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        judged = judge(
            solution=NEVER_RETURNS,
            test_cases=[TestCase(input=[], expected_output=1)],
            limits=LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT,
        )

    shown = judged.test_case_results[0]
    assert caplog.records != []
    assert judged.verdict is Verdict.time_limit_exceeded
    assert shown.verdict is Verdict.time_limit_exceeded
    assert shown.error is None
    assert shown.printed_output == ""
