import json
import os
import sys
import traceback
from multiprocessing.connection import Connection
from typing import Any

from harness.privileges import confine_the_solution

ENTRY_POINT = "solve"


class MissingEntryPoint(Exception):
    pass


def run_solution(solution: str, test_case_input: list[Any], reports: Connection) -> None:
    confine_the_solution()
    capture = _capture_printed_output()
    try:
        returned = _call_entry_point(solution, test_case_input)
        outcome: dict[str, Any] = {"returned": _as_json_value(returned)}
    except BaseException as raised:
        outcome = {"error": _describe(raised)}
    report = outcome | {"printed_output": _read_printed_output(capture)}
    reports.send_bytes(json.dumps(report).encode())
    reports.close()


def _call_entry_point(solution: str, test_case_input: list[Any]) -> Any:
    namespace: dict[str, Any] = {}
    exec(compile(solution, "<solution>", "exec"), namespace)
    entry_point = namespace.get(ENTRY_POINT)
    if not callable(entry_point):
        raise MissingEntryPoint
    return entry_point(*test_case_input)


def _as_json_value(returned: Any) -> Any:
    return json.loads(json.dumps(returned))


def _describe(raised: BaseException) -> str:
    if isinstance(raised, MissingEntryPoint):
        return f"the solution defines no function named {ENTRY_POINT!r}"
    return "".join(traceback.format_exception_only(raised)).strip()


def _capture_printed_output() -> int:
    capture = os.memfd_create("printed-output")
    os.dup2(capture, sys.stdout.fileno())
    os.dup2(capture, sys.stderr.fileno())
    return capture


def _read_printed_output(capture: int) -> str:
    sys.stdout.flush()
    sys.stderr.flush()
    os.lseek(capture, 0, os.SEEK_SET)
    with open(capture, encoding="utf-8", errors="replace") as printed_output:
        return printed_output.read()
