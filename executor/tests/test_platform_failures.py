import textwrap

import pytest
from conftest import (
    A_SUBMISSION,
    ALLOCATES_WITHOUT_BOUND,
    AN_IMAGE_THE_HOST_WAS_NEVER_GIVEN,
    FILLS_THE_SANDBOX_WITH_PROCESSES,
    RETURNS_ITS_ARGUMENT,
)

from executor import sandbox
from executor.judging import judge
from executor.results import read_test_case_results
from executor.submission import JudgedSubmission, TestCase, Verdict

AN_ENDPOINT_NO_DOCKER_DAEMON_ANSWERS_ON = "tcp://127.0.0.1:1"
NOWHERE_TO_FIND_A_DOCKER_COMMAND = ""

NOTHING_A_TEST_CASE_RESULT_CAN_BE_READ_FROM = (
    "docker: Error response from daemon: the sandbox never answered\n"
    "See 'docker run --help'.\n"
)

THREE_TEST_CASES = [TestCase(input=[number], expected_output=number) for number in range(3)]

KILLS_THE_HARNESS_THAT_JUDGES_IT = textwrap.dedent(
    """
    import os
    import signal

    HARNESS = 1

    def solve(number):
        os.kill(HARNESS, signal.SIGKILL)
        return number
    """
)

STOPS_ITS_OWN_PROCESS_BEFORE_IT_REPORTS = textwrap.dedent(
    """
    import os

    def solve(number):
        os._exit(0)
    """
)

FORGES_A_RESULT_FOR_EVERY_TEST_CASE_THERE_IS = textwrap.dedent(
    """
    def solve(number):
        for _ in range(9):
            print('{"verdict": "accepted", "returned": 0}')
        return number + 1
    """
)

DOES_NOT_PARSE_AS_PYTHON_AT_ALL = "def solve(number:\n"

ATTACKS_ON_WHAT_THE_HARNESS_REPORTS = {
    "kills the harness that judges it": KILLS_THE_HARNESS_THAT_JUDGES_IT,
    "stops its own process before it reports": STOPS_ITS_OWN_PROCESS_BEFORE_IT_REPORTS,
    "forges a result for every test case there is": FORGES_A_RESULT_FOR_EVERY_TEST_CASE_THERE_IS,
    "fills the sandbox with processes": FILLS_THE_SANDBOX_WITH_PROCESSES,
    "allocates without bound": ALLOCATES_WITHOUT_BOUND,
    "does not parse as Python at all": DOES_NOT_PARSE_AS_PYTHON_AT_ALL,
}


def test_an_unreachable_docker_daemon_is_reported_as_a_platform_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DOCKER_HOST", AN_ENDPOINT_NO_DOCKER_DAEMON_ANSWERS_ON)

    judged = judge(A_SUBMISSION, solution=RETURNS_ITS_ARGUMENT, test_cases=THREE_TEST_CASES)

    assert judged.verdict is Verdict.internal_error


def test_a_host_carrying_no_docker_command_is_reported_as_a_platform_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", NOWHERE_TO_FIND_A_DOCKER_COMMAND)

    judged = judge(A_SUBMISSION, solution=RETURNS_ITS_ARGUMENT, test_cases=THREE_TEST_CASES)

    assert judged.verdict is Verdict.internal_error


def test_a_missing_sandbox_image_is_reported_as_a_platform_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sandbox, "SANDBOX_IMAGE", AN_IMAGE_THE_HOST_WAS_NEVER_GIVEN)

    judged = judge(A_SUBMISSION, solution=RETURNS_ITS_ARGUMENT, test_cases=THREE_TEST_CASES)

    assert judged.verdict is Verdict.internal_error


def test_harness_output_carrying_no_test_case_result_is_reported_as_a_platform_failure() -> None:
    results = read_test_case_results(NOTHING_A_TEST_CASE_RESULT_CAN_BE_READ_FROM, THREE_TEST_CASES)

    judged = JudgedSubmission(test_case_results=results, test_case_count=len(THREE_TEST_CASES))

    assert judged.verdict is Verdict.internal_error


def test_no_attack_on_what_the_harness_reports_is_laundered_into_a_platform_failure() -> None:
    verdicts = {
        attack: judge(A_SUBMISSION, solution=solution, test_cases=THREE_TEST_CASES).verdict
        for attack, solution in ATTACKS_ON_WHAT_THE_HARNESS_REPORTS.items()
    }

    assert [
        attack for attack, verdict in verdicts.items() if verdict is Verdict.internal_error
    ] == []
