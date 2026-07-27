from collections.abc import Sequence

from executor.limits import Limits, every_limit_named
from executor.logs import (
    a_log_carrying_the_submission_being_judged,
    log_lines_carrying_the_submission,
)
from executor.metrics import count_the_verdict
from executor.results import read_test_case_results
from executor.sandbox import run_sandbox, the_document_a_sandbox_receives
from executor.submission import (
    STOPS_A_SUBMISSION,
    JudgedSubmission,
    TestCase,
    TestCaseResult,
    Verdict,
)


SUBMISSIONS_BEING_JUDGED = a_log_carrying_the_submission_being_judged("executor.judging")


def judge(
    submission_id: str,
    solution: str,
    test_cases: Sequence[TestCase],
    limits: Limits = Limits(),
) -> JudgedSubmission:
    with log_lines_carrying_the_submission(submission_id):
        _record_what_replaying_this_submission_would_need(test_cases, limits)
        emitted = run_sandbox(
            submission_id,
            the_document_a_sandbox_receives(solution, test_cases, limits),
            limits,
        )
        results = read_test_case_results(emitted.stream, test_cases)
        if emitted.killed_from_outside:
            results = _with_the_test_case_it_was_killed_on(results, test_cases)
        judged = JudgedSubmission(
            test_case_results=results,
            test_case_count=len(test_cases),
        )
        count_the_verdict(judged.verdict)
        return judged


def _record_what_replaying_this_submission_would_need(
    test_cases: Sequence[TestCase],
    limits: Limits,
) -> None:
    SUBMISSIONS_BEING_JUDGED.info(
        "judging %d test cases under %s",
        len(test_cases),
        every_limit_named(limits),
    )


def _with_the_test_case_it_was_killed_on(
    results: tuple[TestCaseResult, ...],
    test_cases: Sequence[TestCase],
) -> tuple[TestCaseResult, ...]:
    if len(results) >= len(test_cases) or _had_already_stopped(results):
        return results
    return results + (
        TestCaseResult(
            verdict=Verdict.time_limit_exceeded,
            input=test_cases[len(results)].input,
        ),
    )


def _had_already_stopped(results: tuple[TestCaseResult, ...]) -> bool:
    return bool(results) and results[-1].verdict in STOPS_A_SUBMISSION
