import json
from collections.abc import Sequence
from typing import Any

from executor.submission import (
    VERDICTS_A_TEST_CASE_CAN_REPORT,
    TestCase,
    TestCaseResult,
    Verdict,
)


def read_test_case_results(
    emitted: str,
    test_cases: Sequence[TestCase],
) -> tuple[TestCaseResult, ...]:
    results = []
    for line, test_case in zip(emitted.splitlines(), test_cases):
        result = _read_test_case_result(line, test_case)
        if result is None:
            break
        results.append(result)
    return tuple(results)


def _read_test_case_result(line: str, test_case: TestCase) -> TestCaseResult | None:
    report = _read_json_object(line)
    if report is None:
        return None
    verdict = _read_verdict(report.get("verdict"))
    if verdict is None:
        return None
    printed_output = report.get("printed_output")
    error = report.get("error")
    return TestCaseResult(
        verdict=verdict,
        input=test_case.input,
        returned=report.get("returned"),
        printed_output=printed_output if isinstance(printed_output, str) else "",
        error=error if isinstance(error, str) else None,
    )


def _read_json_object(line: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(line)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _read_verdict(reported: Any) -> Verdict | None:
    if not isinstance(reported, str):
        return None
    try:
        verdict = Verdict(reported)
    except ValueError:
        return None
    return verdict if verdict in VERDICTS_A_TEST_CASE_CAN_REPORT else None
