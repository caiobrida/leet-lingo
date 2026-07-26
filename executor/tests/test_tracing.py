import logging
import subprocess
import textwrap
import time

import pytest
from conftest import (
    SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
)

from executor import sandbox
from executor.judging import judge
from executor.logs import the_executors_log_format
from executor.sandbox import A_NAME_ONLY_OUR_CONTAINERS_CARRY, THE_SUBMISSION_A_CONTAINER_CARRIES
from executor.streams import send_and_collect
from executor.submission import TestCase

RETURNS_ITS_ARGUMENT = textwrap.dedent(
    """
    def solve(number):
        return number
    """
)

WEDGES_ON_ITS_ONLY_TEST_CASE = 0

A_SUBMISSION_FOLLOWED_THROUGH_ITS_LOG_LINES = "submission-followed-through-its-log-lines"
A_SUBMISSION_TRACED_BACK_TO_FROM_ITS_CONTAINER = "submission-traced-back-to-from-its-container"

LONGEST_A_CONTAINER_TAKES_TO_REACH_THE_DAEMON = 10.0


def test_every_log_line_emitted_while_judging_names_the_submission_it_came_from(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        judge(
            A_SUBMISSION_FOLLOWED_THROUGH_ITS_LOG_LINES,
            solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
            test_cases=[TestCase(input=[0, WEDGES_ON_ITS_ONLY_TEST_CASE], expected_output=0)],
            limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
        )

    lines = [the_executors_log_format().format(record) for record in caplog.records]
    assert lines != []
    assert [line for line in lines if A_SUBMISSION_FOLLOWED_THROUGH_ITS_LOG_LINES in line] == lines


def test_a_container_can_be_traced_back_to_the_submission_that_created_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    traced: list[str] = []

    def trace_the_container_while_it_is_still_judging(
        process: "subprocess.Popen[str]",
        payload: str,
    ) -> str:
        traced.extend(_containers_labelled_with(A_SUBMISSION_TRACED_BACK_TO_FROM_ITS_CONTAINER))
        return send_and_collect(process, payload)

    monkeypatch.setattr(sandbox, "send_and_collect", trace_the_container_while_it_is_still_judging)

    judge(
        A_SUBMISSION_TRACED_BACK_TO_FROM_ITS_CONTAINER,
        solution=RETURNS_ITS_ARGUMENT,
        test_cases=[TestCase(input=[1], expected_output=1)],
    )

    assert len(traced) == 1
    assert traced[0].startswith(A_NAME_ONLY_OUR_CONTAINERS_CARRY)


def _containers_labelled_with(submission_id: str) -> list[str]:
    give_up_at = time.monotonic() + LONGEST_A_CONTAINER_TAKES_TO_REACH_THE_DAEMON
    while time.monotonic() < give_up_at:
        listed = subprocess.run(
            [
                "docker",
                "ps",
                "--all",
                "--format",
                "{{.Names}}",
                "--filter",
                f"label={THE_SUBMISSION_A_CONTAINER_CARRIES}={submission_id}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        if listed.stdout.split():
            return listed.stdout.split()
    return []
