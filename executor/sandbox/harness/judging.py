import json
import multiprocessing
from collections.abc import Iterator
from multiprocessing.connection import Connection
from typing import Any

from harness.child import run_solution
from harness.memory_limit import has_killed_a_process
from harness.payload import TestCase

ACCEPTED = "accepted"
WRONG_ANSWER = "wrong_answer"
RUNTIME_ERROR = "runtime_error"
MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"

STOPPED_WITHOUT_REPORTING = "the solution stopped before it returned a value"
NO_ROOM_LEFT_FOR_A_PROCESS = (
    "the solution left the sandbox no room to start a process for this test case"
)


def judge_test_cases(solution: str, test_cases: list[TestCase]) -> Iterator[dict[str, Any]]:
    for test_case in test_cases:
        result = _judge_test_case(solution, test_case)
        yield result
        if result["verdict"] == MEMORY_LIMIT_EXCEEDED:
            return


def _judge_test_case(solution: str, test_case: TestCase) -> dict[str, Any]:
    report = _run_in_child_process(solution, test_case.input)
    if report is not None:
        return _test_case_result(report, test_case.expected_output)
    if has_killed_a_process():
        return {"verdict": MEMORY_LIMIT_EXCEEDED, "printed_output": ""}
    return {
        "verdict": RUNTIME_ERROR,
        "error": STOPPED_WITHOUT_REPORTING,
        "printed_output": "",
    }


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


def _run_in_child_process(solution: str, test_case_input: list[Any]) -> dict[str, Any] | None:
    reports, sent_by_the_child = multiprocessing.Pipe(duplex=False)
    child = multiprocessing.Process(
        target=run_solution,
        args=(solution, test_case_input, sent_by_the_child),
    )
    started = _start(child)
    sent_by_the_child.close()
    if not started:
        reports.close()
        return {"error": NO_ROOM_LEFT_FOR_A_PROCESS}
    try:
        return _read_report(reports)
    finally:
        reports.close()
        child.join()


def _start(child: multiprocessing.Process) -> bool:
    try:
        child.start()
    except OSError:
        return False
    return True


def _read_report(reports: Connection) -> dict[str, Any] | None:
    try:
        report = json.loads(reports.recv_bytes())
    except (EOFError, OSError, ValueError):
        return None
    if isinstance(report, dict) and ("returned" in report or "error" in report):
        return report
    return None
