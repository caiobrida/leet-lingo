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


STOPS_A_SUBMISSION = frozenset({Verdict.time_limit_exceeded, Verdict.memory_limit_exceeded})


@dataclass(frozen=True)
class TestCase:
    input: list[Any]
    expected_output: Any


@dataclass(frozen=True)
class TestCaseResult:
    verdict: Verdict
    input: list[Any]
    returned: Any = None
    printed_output: str = ""
    error: str | None = None


@dataclass(frozen=True)
class JudgedSubmission:
    test_case_results: tuple[TestCaseResult, ...]
    test_case_count: int

    @property
    def verdict(self) -> Verdict:
        if not self.test_case_results:
            return Verdict.internal_error
        if not self._reported_on_every_test_case and not self._stopped_by_a_limit:
            return Verdict.internal_error
        for result in self.test_case_results:
            if result.verdict is not Verdict.accepted:
                return result.verdict
        return Verdict.accepted

    @property
    def _reported_on_every_test_case(self) -> bool:
        return len(self.test_case_results) == self.test_case_count

    @property
    def _stopped_by_a_limit(self) -> bool:
        return self.test_case_results[-1].verdict in STOPS_A_SUBMISSION
