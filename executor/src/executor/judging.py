import json
from collections.abc import Sequence

from executor.limits import Limits
from executor.results import read_test_case_results
from executor.sandbox import run_sandbox
from executor.submission import JudgedSubmission, TestCase, TestCaseResult, Verdict


def judge(
    solution: str,
    test_cases: Sequence[TestCase],
    limits: Limits = Limits(),
) -> JudgedSubmission:
    run = run_sandbox(_payload(solution, test_cases, limits), limits)
    results = read_test_case_results(run.emitted, test_cases)
    if run.killed_from_outside:
        results = _with_the_test_case_it_was_killed_on(results, test_cases)
    return JudgedSubmission(test_case_results=results, test_case_count=len(test_cases))


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
    if len(results) >= len(test_cases):
        return results
    return results + (
        TestCaseResult(
            verdict=Verdict.time_limit_exceeded,
            input=test_cases[len(results)].input,
        ),
    )
