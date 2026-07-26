import subprocess
from typing import IO, cast

import pytest
from conftest import (
    SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
    containers_still_on_the_host,
)

from executor import sandbox
from executor.judging import judge
from executor.sandbox import SANDBOX_IMAGE
from executor.submission import TestCase, Verdict

WEDGES_ON_ITS_ONLY_TEST_CASE = 0
WEDGES_ONCE_THE_FIRST_TEST_CASE_IS_ANSWERED = 1

TEST_CASES_WEDGED_AFTER_THE_FIRST = [
    TestCase(input=[number, WEDGES_ONCE_THE_FIRST_TEST_CASE_IS_ANSWERED], expected_output=number)
    for number in range(2)
]

SUBMISSIONS_ENOUGH_TO_SHOW_CONTAINERS_PILING_UP = 3


class JudgingFailedPartway(Exception):
    pass


def test_no_container_outlives_the_submission_that_created_it() -> None:
    judge(
        solution="def solve():\n    return 1\n",
        test_cases=[TestCase(input=[], expected_output=1)],
    )

    assert containers_still_on_the_host() == []


def test_no_container_outlives_a_submission_killed_from_outside() -> None:
    judge(
        solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
        test_cases=[TestCase(input=[0, WEDGES_ON_ITS_ONLY_TEST_CASE], expected_output=0)],
        limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    )

    assert containers_still_on_the_host() == []


def test_no_container_outlives_a_submission_whose_judging_failed_partway(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sandbox, "send_and_collect", _fail_once_the_sandbox_is_judging)

    with pytest.raises(JudgingFailedPartway):
        judge(
            solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
            test_cases=TEST_CASES_WEDGED_AFTER_THE_FIRST,
            limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
        )

    assert containers_still_on_the_host() == []


def test_repeated_failures_do_not_accumulate_containers_on_the_host() -> None:
    for _ in range(SUBMISSIONS_ENOUGH_TO_SHOW_CONTAINERS_PILING_UP):
        judged = judge(
            solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
            test_cases=[TestCase(input=[0, WEDGES_ON_ITS_ONLY_TEST_CASE], expected_output=0)],
            limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
        )

        assert judged.verdict is Verdict.time_limit_exceeded

    assert containers_still_on_the_host() == []


def test_the_sandbox_image_installs_no_third_party_packages() -> None:
    installed = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "python", SANDBOX_IMAGE, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert installed.stdout.split() == []


def _fail_once_the_sandbox_is_judging(process: "subprocess.Popen[str]", payload: str) -> str:
    with cast(IO[str], process.stdin) as stdin:
        stdin.write(payload)
    cast(IO[str], process.stdout).readline()
    raise JudgingFailedPartway
