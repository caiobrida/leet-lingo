import json
from collections.abc import Sequence

from executor.limits import Limits
from executor.logs import log_lines_carrying_the_submission
from executor.metrics import count_the_verdict
from executor.results import read_test_case_results
from executor.sandbox import run_sandbox
from executor.submission import (
    STOPS_A_SUBMISSION,
    JudgedSubmission,
    TestCase,
    TestCaseResult,
    Verdict,
)


def judge(
    submission_id: str,
    solution: str,
    test_cases: Sequence[TestCase],
    limits: Limits = Limits(),
) -> JudgedSubmission:
    with log_lines_carrying_the_submission(submission_id):
        emitted = run_sandbox(submission_id, _payload(solution, test_cases, limits), limits)
        results = read_test_case_results(emitted.stream, test_cases)
        if emitted.killed_from_outside:
            results = _with_the_test_case_it_was_killed_on(results, test_cases)
        judged = JudgedSubmission(
            test_case_results=results,
            test_case_count=len(test_cases),
        )
        count_the_verdict(judged.verdict)
        return judged


def _payload(solution: str, test_cases: Sequence[TestCase], limits: Limits) -> str:
    return json.dumps(
        {
            "solution": solution,
            "test_cases": [
                {"input": test_case.input, "expected_output": test_case.expected_output}
                for test_case in test_cases
            ],
            "limits": {
                "test_case_seconds": limits.test_case_seconds,
                "submission_seconds": limits.submission_seconds,
            },
        }
    )


def _with_the_test_case_it_was_killed_on(
    results: tuple[TestCaseResult, ...],
    test_cases: Sequence[TestCase],
) -> tuple[TestCaseResult, ...]:
    if len(results) >= len(test_cases) or _had_already_stopped(results):
        return results
    return results + (
        TestCaseResult(
            verdict=Verdict.time_limit_exceeded,
            input=test_cases[len(results)].input,
        ),
    )


def _had_already_stopped(results: tuple[TestCaseResult, ...]) -> bool:
    return bool(results) and results[-1].verdict in STOPS_A_SUBMISSION
