import json
import multiprocessing
import time
from collections.abc import Iterator
from dataclasses import dataclass
from multiprocessing.connection import Connection
from typing import Any

from harness.child import run_solution
from harness.memory_limit import has_killed_a_process_since, processes_the_memory_limit_has_killed
from harness.payload import Limits, TestCase
from harness.solution_processes import kill_everything_the_solution_started

ACCEPTED = "accepted"
WRONG_ANSWER = "wrong_answer"
RUNTIME_ERROR = "runtime_error"
MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
TIME_LIMIT_EXCEEDED = "time_limit_exceeded"

STOPPED_WITHOUT_REPORTING = "the solution stopped before it returned a value"
NO_ROOM_LEFT_FOR_A_PROCESS = (
    "the solution left the sandbox no room to start a process for this test case"
)


@dataclass(frozen=True)
class SolutionReport:
    report: dict[str, Any] | None
    ran_out_of_time: bool = False


def judge_test_cases(
    solution: str,
    test_cases: list[TestCase],
    limits: Limits,
) -> Iterator[dict[str, Any]]:
    budget_ends_at = time.monotonic() + limits.submission_seconds
    for test_case in test_cases:
        if time.monotonic() >= budget_ends_at:
            yield _out_of_time()
            return
        result = _judge_test_case(solution, test_case, limits.test_case_seconds)
        yield result
        if result["verdict"] == MEMORY_LIMIT_EXCEEDED:
            return


def _judge_test_case(solution: str, test_case: TestCase, seconds: float) -> dict[str, Any]:
    killed_before_the_test_case = processes_the_memory_limit_has_killed()
    reported = _run_in_child_process(solution, test_case.input, seconds)
    if reported.report is not None:
        return _test_case_result(reported.report, test_case.expected_output)
    if reported.ran_out_of_time:
        return _out_of_time()
    if has_killed_a_process_since(killed_before_the_test_case):
        return {"verdict": MEMORY_LIMIT_EXCEEDED, "printed_output": ""}
    return {
        "verdict": RUNTIME_ERROR,
        "error": STOPPED_WITHOUT_REPORTING,
        "printed_output": "",
    }


def _out_of_time() -> dict[str, Any]:
    return {"verdict": TIME_LIMIT_EXCEEDED, "printed_output": ""}


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


def _run_in_child_process(
    solution: str,
    test_case_input: list[Any],
    seconds: float,
) -> SolutionReport:
    reports, sent_by_the_child = multiprocessing.Pipe(duplex=False)
    child = multiprocessing.Process(
        target=run_solution,
        args=(solution, test_case_input, sent_by_the_child),
    )
    started = _start(child)
    sent_by_the_child.close()
    if not started:
        reports.close()
        return SolutionReport(report={"error": NO_ROOM_LEFT_FOR_A_PROCESS})
    try:
        if not reports.poll(seconds):
            return SolutionReport(report=None, ran_out_of_time=True)
        return SolutionReport(report=_read_report(reports))
    finally:
        reports.close()
        _stop(child)


def _start(child: multiprocessing.Process) -> bool:
    try:
        child.start()
    except OSError:
        return False
    return True


def _stop(child: multiprocessing.Process) -> None:
    child.kill()
    child.join()
    kill_everything_the_solution_started()


def _read_report(reports: Connection) -> dict[str, Any] | None:
    try:
        report = json.loads(reports.recv_bytes())
    except (EOFError, OSError, ValueError):
        return None
    if isinstance(report, dict) and ("returned" in report or "error" in report):
        return report
    return None
