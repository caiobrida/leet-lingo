import logging
import textwrap

import pytest
from conftest import AN_IMAGE_THE_HOST_WAS_NEVER_GIVEN, RETURNS_ITS_ARGUMENT
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from executor import sandbox
from executor.judging import judge
from executor.metrics import the_metrics_an_operator_scrapes
from executor.submission import TestCase, Verdict

SUBMISSIONS_AN_OPERATOR_COUNTS = "submissions_judged_total"
THE_DIMENSION_A_VERDICT_IS_COUNTED_ON = "verdict"

RETURNS_ONE_MORE_THAN_ITS_ARGUMENT = textwrap.dedent(
    """
    def solve(number):
        return number + 1
    """
)

FORGES_THE_TELEMETRY_OF_A_SUBMISSION_THAT_WENT_WELL = textwrap.dedent(
    """
    import sys

    def solve(number):
        print('submissions_judged_total{verdict="accepted"} 99')
        sys.stderr.write("the sandbox stopped enforcing its own timeouts\\n")
        return number + 1
    """
)

A_SUBMISSION_COUNTED_UNDER_THE_VERDICT_IT_EARNED = "submission-counted-under-the-verdict-it-earned"
A_SUBMISSION_NO_SANDBOX_IMAGE_ANSWERS = "submission-no-sandbox-image-answers"
A_SUBMISSION_SCRAPED_BY_AN_OPERATOR = "submission-scraped-by-an-operator"
A_SUBMISSION_FORGING_ITS_OWN_TELEMETRY = "submission-forging-its-own-telemetry"
A_SUBMISSION_COUNTED_WHEN_IT_ARRIVED_OVER_HTTP = "submission-counted-when-it-arrived-over-http"

ONE_TEST_CASE_THE_SOLUTION_GETS_WRONG = [TestCase(input=[1], expected_output=1)]


def test_a_verdict_is_counted_as_a_metric_dimension_rather_than_only_written_to_a_log() -> None:
    counted_before = _submissions_counted_as(Verdict.wrong_answer)

    judge(
        A_SUBMISSION_COUNTED_UNDER_THE_VERDICT_IT_EARNED,
        solution=RETURNS_ONE_MORE_THAN_ITS_ARGUMENT,
        test_cases=ONE_TEST_CASE_THE_SOLUTION_GETS_WRONG,
    )

    assert _submissions_counted_as(Verdict.wrong_answer) == counted_before + 1


def test_a_platform_failure_is_counted_apart_from_every_verdict_a_solution_can_earn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sandbox, "SANDBOX_IMAGE", AN_IMAGE_THE_HOST_WAS_NEVER_GIVEN)
    counted_before = _every_verdict_counted()

    judge(
        A_SUBMISSION_NO_SANDBOX_IMAGE_ANSWERS,
        solution=RETURNS_ONE_MORE_THAN_ITS_ARGUMENT,
        test_cases=ONE_TEST_CASE_THE_SOLUTION_GETS_WRONG,
    )

    assert _the_verdicts_counted_since(counted_before) == {Verdict.internal_error}


def test_the_metrics_an_operator_scrapes_name_the_verdict_each_submission_was_counted_under(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sandbox, "SANDBOX_IMAGE", AN_IMAGE_THE_HOST_WAS_NEVER_GIVEN)

    judge(
        A_SUBMISSION_SCRAPED_BY_AN_OPERATOR,
        solution=RETURNS_ONE_MORE_THAN_ITS_ARGUMENT,
        test_cases=ONE_TEST_CASE_THE_SOLUTION_GETS_WRONG,
    )

    scraped = the_metrics_an_operator_scrapes().decode()
    assert _a_series_counting(Verdict.internal_error) in scraped


def test_nothing_a_solution_emits_from_inside_the_sandbox_reaches_what_an_operator_reads(
    caplog: pytest.LogCaptureFixture,
) -> None:
    counted_before = _every_verdict_counted()

    with caplog.at_level(logging.WARNING):
        judged = judge(
            A_SUBMISSION_FORGING_ITS_OWN_TELEMETRY,
            solution=FORGES_THE_TELEMETRY_OF_A_SUBMISSION_THAT_WENT_WELL,
            test_cases=ONE_TEST_CASE_THE_SOLUTION_GETS_WRONG,
        )

    assert judged.verdict is Verdict.wrong_answer
    assert caplog.records == []
    assert _the_verdicts_counted_since(counted_before) == {Verdict.wrong_answer}


def test_a_verdict_is_counted_the_same_when_the_submission_arrived_over_http(
    executor: TestClient,
) -> None:
    counted_before = _submissions_counted_as(Verdict.accepted)

    answered = executor.post(
        "/submissions",
        json={
            "submission_id": A_SUBMISSION_COUNTED_WHEN_IT_ARRIVED_OVER_HTTP,
            "solution": RETURNS_ITS_ARGUMENT,
            "test_cases": [{"input": [1], "expected_output": 1}],
        },
    )

    assert answered.json()["verdict"] == Verdict.accepted.value
    assert _submissions_counted_as(Verdict.accepted) == counted_before + 1


def _a_series_counting(verdict: Verdict) -> str:
    return (
        f'{SUBMISSIONS_AN_OPERATOR_COUNTS}{{{THE_DIMENSION_A_VERDICT_IS_COUNTED_ON}='
        f'"{verdict.value}"}}'
    )


def _submissions_counted_as(verdict: Verdict) -> float:
    counted = REGISTRY.get_sample_value(
        SUBMISSIONS_AN_OPERATOR_COUNTS,
        {THE_DIMENSION_A_VERDICT_IS_COUNTED_ON: verdict.value},
    )
    return 0.0 if counted is None else counted


def _every_verdict_counted() -> dict[Verdict, float]:
    return {verdict: _submissions_counted_as(verdict) for verdict in Verdict}


def _the_verdicts_counted_since(counted_before: dict[Verdict, float]) -> set[Verdict]:
    counted_now = _every_verdict_counted()
    return {verdict for verdict in Verdict if counted_now[verdict] != counted_before[verdict]}
