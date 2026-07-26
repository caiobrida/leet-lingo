import json
from dataclasses import dataclass
from typing import Any


class InvalidPayload(Exception):
    pass


@dataclass(frozen=True)
class TestCase:
    input: list[Any]
    expected_output: Any


@dataclass(frozen=True)
class Limits:
    test_case_seconds: float
    submission_seconds: float


@dataclass(frozen=True)
class Payload:
    solution: str
    test_cases: list[TestCase]
    limits: Limits


def parse_payload(document: str) -> Payload:
    try:
        parsed = json.loads(document)
    except ValueError:
        raise InvalidPayload("the payload is not a JSON document")
    if not isinstance(parsed, dict):
        raise InvalidPayload("the payload is not a JSON object")
    return Payload(
        solution=_read_solution(parsed),
        test_cases=[_read_test_case(entry) for entry in _read_test_case_entries(parsed)],
        limits=_read_limits(parsed),
    )


def _read_solution(parsed: dict[str, Any]) -> str:
    solution = parsed.get("solution")
    if not isinstance(solution, str):
        raise InvalidPayload("the payload carries no solution")
    return solution


def _read_test_case_entries(parsed: dict[str, Any]) -> list[Any]:
    entries = parsed.get("test_cases")
    if not isinstance(entries, list):
        raise InvalidPayload("the payload carries no test cases")
    return entries


def _read_test_case(entry: Any) -> TestCase:
    if not isinstance(entry, dict):
        raise InvalidPayload("a test case is not a JSON object")
    test_case_input = entry.get("input")
    if not isinstance(test_case_input, list):
        raise InvalidPayload("a test case input is not a list of arguments")
    if "expected_output" not in entry:
        raise InvalidPayload("a test case carries no expected output")
    return TestCase(input=test_case_input, expected_output=entry["expected_output"])


def _read_limits(parsed: dict[str, Any]) -> Limits:
    limits = parsed.get("limits")
    if not isinstance(limits, dict):
        raise InvalidPayload("the payload carries no limits")
    return Limits(
        test_case_seconds=_read_seconds(limits, "test_case_seconds"),
        submission_seconds=_read_seconds(limits, "submission_seconds"),
    )


def _read_seconds(limits: dict[str, Any], name: str) -> float:
    seconds = limits.get(name)
    if not isinstance(seconds, int | float) or seconds <= 0:
        raise InvalidPayload(f"the limit {name} is not a positive number of seconds")
    return float(seconds)
