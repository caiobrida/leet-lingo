from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    accepted = "accepted"
    wrong_answer = "wrong_answer"
    time_limit_exceeded = "time_limit_exceeded"
    runtime_error = "runtime_error"
    memory_limit_exceeded = "memory_limit_exceeded"
    internal_error = "internal_error"


@dataclass(frozen=True)
class TestCase:
    input: list[Any]
    expected_output: Any


@dataclass(frozen=True)
class TestCaseResult:
    verdict: Verdict


@dataclass(frozen=True)
class JudgedSubmission:
    test_case_results: tuple[TestCaseResult, ...]
    test_case_count: int

    @property
    def verdict(self) -> Verdict:
        if len(self.test_case_results) != self.test_case_count:
            return Verdict.internal_error
        for result in self.test_case_results:
            if result.verdict is not Verdict.accepted:
                return result.verdict
        return Verdict.accepted
