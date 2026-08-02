import threading
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from executor import main
from executor.limits import Limits
from executor.submission import JudgedSubmission, TestCase, TestCaseResult, Verdict

A_SUBMISSION_ANSWERED_WITH_ITS_VERDICT = "submission-answered-with-its-verdict"
A_SUBMISSION_ANSWERED_WITH_A_RESULT_PER_TEST_CASE = "submission-answered-with-a-result-per-test-case"
A_SUBMISSION_KILLED_BEFORE_ITS_LAST_TEST_CASE = "submission-killed-before-its-last-test-case"
A_SUBMISSION_NEVER_TOLD_WHAT_IT_WAS_JUDGED_AGAINST = (
    "submission-never-told-what-it-was-judged-against"
)
A_SUBMISSION_THE_EXECUTOR_NEVER_RENAMES = "submission-the-executor-never-renames"
A_SUBMISSION_JUDGED_AS_IT_ARRIVED = "submission-judged-as-it-arrived"
A_SUBMISSION_NAMING_THE_LIMITS_IT_IS_JUDGED_UNDER = "submission-naming-the-limits-it-is-judged-under"
A_SUBMISSION_NAMING_NO_LIMITS_AT_ALL = "submission-naming-no-limits-at-all"
A_SUBMISSION_WITH_NOTHING_TO_JUDGE_IT_AGAINST = "submission-with-nothing-to-judge-it-against"
A_SUBMISSION_LEET_LINGO_FAILED_TO_JUDGE = "submission-leet-lingo-failed-to-judge"
A_SUBMISSION_HELD_WHILE_THE_EXECUTOR_ANSWERS_SOMETHING_ELSE = (
    "submission-held-while-the-executor-answers-something-else"
)

A_SOLUTION_NOTHING_IN_THIS_FILE_EVER_RUNS = "def solve(number):\n    return number + 1\n"

THREE_TEST_CASES_SENT = [
    {"input": [1], "expected_output": 2},
    {"input": [2], "expected_output": 3},
    {"input": [3], "expected_output": 4},
]

THE_THREE_TEST_CASES_THAT_ARRIVE = (
    TestCase(input=[1], expected_output=2),
    TestCase(input=[2], expected_output=3),
    TestCase(input=[3], expected_output=4),
)

LIMITS_SENT_WITH_THE_SUBMISSION = {
    "test_case_seconds": 0.5,
    "submission_seconds": 3.0,
    "sandbox_seconds": 6.0,
    "memory_bytes": 64 * 1024 * 1024,
    "cpus": 0.5,
    "processes": 8,
}

THE_LIMITS_THAT_ARRIVE = Limits(
    test_case_seconds=0.5,
    submission_seconds=3.0,
    sandbox_seconds=6.0,
    memory_bytes=64 * 1024 * 1024,
    cpus=0.5,
    processes=8,
)

JUDGED_ACROSS_THREE_TEST_CASES = JudgedSubmission(
    test_case_results=(
        TestCaseResult(
            verdict=Verdict.accepted,
            input=[1],
            returned=2,
            printed_output="halfway there\n",
        ),
        TestCaseResult(verdict=Verdict.wrong_answer, input=[2], returned=4),
        TestCaseResult(
            verdict=Verdict.runtime_error,
            input=[3],
            error="ZeroDivisionError: division by zero",
        ),
    ),
    test_case_count=3,
)

JUDGED_UNTIL_THE_SUBMISSION_WAS_KILLED = JudgedSubmission(
    test_case_results=(
        TestCaseResult(verdict=Verdict.accepted, input=[1], returned=2),
        TestCaseResult(verdict=Verdict.time_limit_exceeded, input=[2]),
    ),
    test_case_count=3,
)

JUDGED_AS_LEET_LINGO_FAILING = JudgedSubmission(test_case_results=(), test_case_count=3)

LONGEST_A_HELD_SUBMISSION_WAITS_TO_BE_RELEASED = 5.0


@dataclass(frozen=True)
class SubmissionGivenToJudging:
    submission_id: str
    solution: str
    test_cases: tuple[TestCase, ...]
    limits: Limits


@dataclass
class JudgingThatAnswers:
    answers: JudgedSubmission
    was_given: list[SubmissionGivenToJudging] = field(default_factory=list)

    def __call__(
        self,
        submission_id: str,
        solution: str,
        test_cases: Sequence[TestCase],
        limits: Limits,
    ) -> JudgedSubmission:
        self.was_given.append(
            SubmissionGivenToJudging(submission_id, solution, tuple(test_cases), limits)
        )
        return self.answers


def test_a_submission_sent_over_http_is_answered_with_the_verdict_it_earned(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    answered = executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_ANSWERED_WITH_ITS_VERDICT),
    )

    assert answered.status_code == 200
    assert answered.json()["verdict"] == Verdict.wrong_answer.value


def test_every_test_case_a_submission_reached_is_answered_with_what_the_solution_did(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    answered = executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_ANSWERED_WITH_A_RESULT_PER_TEST_CASE),
    )

    assert answered.json()["test_case_results"] == [
        {
            "verdict": "accepted",
            "input": [1],
            "returned": 2,
            "printed_output": "halfway there\n",
            "error": None,
        },
        {
            "verdict": "wrong_answer",
            "input": [2],
            "returned": 4,
            "printed_output": "",
            "error": None,
        },
        {
            "verdict": "runtime_error",
            "input": [3],
            "returned": None,
            "printed_output": "",
            "error": "ZeroDivisionError: division by zero",
        },
    ]


def test_a_submission_killed_partway_is_answered_with_only_the_test_cases_it_reached(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _judging_that_answers(monkeypatch, JUDGED_UNTIL_THE_SUBMISSION_WAS_KILLED)

    answered = executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_KILLED_BEFORE_ITS_LAST_TEST_CASE),
    )

    assert answered.json()["verdict"] == Verdict.time_limit_exceeded.value
    assert [result["input"] for result in answered.json()["test_case_results"]] == [[1], [2]]


def test_what_a_correct_solution_should_have_returned_is_never_answered_to_the_caller(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    answered = executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_NEVER_TOLD_WHAT_IT_WAS_JUDGED_AGAINST),
    )

    assert "expected_output" not in answered.text


def test_the_identifier_the_caller_sent_is_the_one_the_submission_is_judged_under(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging = _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_THE_EXECUTOR_NEVER_RENAMES),
    )

    assert [given.submission_id for given in judging.was_given] == [
        A_SUBMISSION_THE_EXECUTOR_NEVER_RENAMES
    ]


def test_a_submission_is_judged_with_the_solution_and_test_cases_that_arrived_with_it(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging = _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    executor.post("/submissions", json=_a_submission(A_SUBMISSION_JUDGED_AS_IT_ARRIVED))

    assert [(given.solution, given.test_cases) for given in judging.was_given] == [
        (A_SOLUTION_NOTHING_IN_THIS_FILE_EVER_RUNS, THE_THREE_TEST_CASES_THAT_ARRIVE)
    ]


def test_a_submission_is_judged_under_the_limits_that_arrived_with_it(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging = _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_NAMING_THE_LIMITS_IT_IS_JUDGED_UNDER),
    )

    assert [given.limits for given in judging.was_given] == [THE_LIMITS_THAT_ARRIVE]


def test_a_submission_naming_no_limits_is_refused_rather_than_judged_under_the_executors_own(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging = _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    refused = executor.post(
        "/submissions",
        json={
            "submission_id": A_SUBMISSION_NAMING_NO_LIMITS_AT_ALL,
            "solution": A_SOLUTION_NOTHING_IN_THIS_FILE_EVER_RUNS,
            "test_cases": THREE_TEST_CASES_SENT,
        },
    )

    assert refused.status_code == 422
    assert judging.was_given == []


def test_the_executor_answers_that_it_judged_even_when_the_verdict_is_that_leet_lingo_failed(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _judging_that_answers(monkeypatch, JUDGED_AS_LEET_LINGO_FAILING)

    answered = executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_LEET_LINGO_FAILED_TO_JUDGE),
    )

    assert answered.status_code == 200
    assert answered.json() == {"verdict": Verdict.internal_error.value, "test_case_results": []}


def test_a_payload_the_executor_cannot_read_is_refused_before_anything_is_judged(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging = _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    refused = executor.post("/submissions", json={"test_cases": "not a list of test cases"})

    assert refused.status_code == 422
    assert judging.was_given == []
    assert Verdict.internal_error.value not in refused.text


def test_a_submission_with_nothing_to_judge_it_against_is_refused_rather_than_judged(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging = _judging_that_answers(monkeypatch, JUDGED_ACROSS_THREE_TEST_CASES)

    refused = executor.post(
        "/submissions",
        json=_a_submission(A_SUBMISSION_WITH_NOTHING_TO_JUDGE_IT_AGAINST, test_cases=[]),
    )

    assert refused.status_code == 422
    assert judging.was_given == []
    assert Verdict.internal_error.value not in refused.text


def test_a_submission_being_judged_does_not_stop_the_executor_answering_anything_else(
    executor: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    judging_began = threading.Event()
    something_else_was_answered = threading.Event()
    held_until_something_else_was_answered: list[bool] = []

    def judging_held_while_the_executor_is_asked_something_else(*_: Any) -> JudgedSubmission:
        judging_began.set()
        held_until_something_else_was_answered.append(
            something_else_was_answered.wait(LONGEST_A_HELD_SUBMISSION_WAITS_TO_BE_RELEASED)
        )
        return JUDGED_ACROSS_THREE_TEST_CASES

    monkeypatch.setattr(main, "judge", judging_held_while_the_executor_is_asked_something_else)

    judging = threading.Thread(
        target=lambda: executor.post(
            "/submissions",
            json=_a_submission(A_SUBMISSION_HELD_WHILE_THE_EXECUTOR_ANSWERS_SOMETHING_ELSE),
        )
    )
    judging.start()
    try:
        assert judging_began.wait(LONGEST_A_HELD_SUBMISSION_WAITS_TO_BE_RELEASED)
        answered = executor.get("/health")
    finally:
        something_else_was_answered.set()
        judging.join(LONGEST_A_HELD_SUBMISSION_WAITS_TO_BE_RELEASED)

    assert answered.status_code == 200
    assert held_until_something_else_was_answered == [True]


def _judging_that_answers(
    monkeypatch: pytest.MonkeyPatch,
    judged: JudgedSubmission,
) -> JudgingThatAnswers:
    judging = JudgingThatAnswers(judged)
    monkeypatch.setattr(main, "judge", judging)
    return judging


def _a_submission(submission_id: str, **also_sent: Any) -> dict[str, Any]:
    return {
        "submission_id": submission_id,
        "solution": A_SOLUTION_NOTHING_IN_THIS_FILE_EVER_RUNS,
        "test_cases": THREE_TEST_CASES_SENT,
        "limits": LIMITS_SENT_WITH_THE_SUBMISSION,
    } | also_sent
