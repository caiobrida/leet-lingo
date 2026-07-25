import json
import multiprocessing
from collections.abc import Iterator
from multiprocessing.connection import Connection
from typing import Any

from harness.child import run_solution
from harness.payload import TestCase

ACCEPTED = "accepted"
WRONG_ANSWER = "wrong_answer"
RUNTIME_ERROR = "runtime_error"

STOPPED_WITHOUT_REPORTING = "the solution stopped before it returned a value"


def judge_test_cases(solution: str, test_cases: list[TestCase]) -> Iterator[dict[str, Any]]:
    for test_case in test_cases:
        report = _run_in_child_process(solution, test_case.input)
        yield _test_case_result(report, test_case.expected_output)


def _test_case_result(report: dict[str, Any], expected_output: Any) -> dict[str, Any]:
    printed_output = report.get("printed_output", "")
    if "error" in report:
        return {
            "verdict": RUNTIME_ERROR,
            "error": report["error"],
            "printed_output": printed_output,
        }
    returned = report["returned"]
    passed = returned == expected_output
    return {
        "verdict": ACCEPTED if passed else WRONG_ANSWER,
        "returned": returned,
        "printed_output": printed_output,
    }


def _run_in_child_process(solution: str, test_case_input: list[Any]) -> dict[str, Any]:
    reports, sent_by_the_child = multiprocessing.Pipe(duplex=False)
    child = multiprocessing.Process(
        target=run_solution,
        args=(solution, test_case_input, sent_by_the_child),
    )
    child.start()
    sent_by_the_child.close()
    try:
        return _read_report(reports)
    finally:
        reports.close()
        child.join()


def _read_report(reports: Connection) -> dict[str, Any]:
    try:
        report = json.loads(reports.recv_bytes())
    except (EOFError, OSError, ValueError):
        report = None
    if isinstance(report, dict) and ("returned" in report or "error" in report):
        return report
    return {"error": STOPPED_WITHOUT_REPORTING}
