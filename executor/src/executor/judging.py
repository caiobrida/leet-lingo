import json
from collections.abc import Sequence

from executor.limits import Limits
from executor.sandbox import run_sandbox
from executor.submission import JudgedSubmission, TestCase, TestCaseResult, Verdict


def judge(
    solution: str,
    test_cases: Sequence[TestCase],
    limits: Limits = Limits(),
) -> JudgedSubmission:
    emitted = run_sandbox(_payload(solution, test_cases), limits)
    return JudgedSubmission(
        test_case_results=_read_test_case_results(emitted),
        test_case_count=len(test_cases),
    )


def _payload(solution: str, test_cases: Sequence[TestCase]) -> str:
    return json.dumps(
        {
            "solution": solution,
            "test_cases": [
                {"input": test_case.input, "expected_output": test_case.expected_output}
                for test_case in test_cases
            ],
        }
    )


def _read_test_case_results(emitted: str) -> tuple[TestCaseResult, ...]:
    results = []
    for line in emitted.splitlines():
        verdict = _read_verdict(line)
        if verdict is not None:
            results.append(TestCaseResult(verdict=verdict))
    return tuple(results)


def _read_verdict(line: str) -> Verdict | None:
    try:
        emitted = json.loads(line)
    except ValueError:
        return None
    if not isinstance(emitted, dict):
        return None
    verdict = emitted.get("verdict")
    if not isinstance(verdict, str):
        return None
    try:
        return Verdict(verdict)
    except ValueError:
        return None
