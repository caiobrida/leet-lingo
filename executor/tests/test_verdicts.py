from executor.submission import JudgedSubmission, TestCaseResult, Verdict


def test_a_submission_whose_test_case_results_all_passed_is_accepted() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(input=[], verdict=Verdict.accepted),
            TestCaseResult(input=[], verdict=Verdict.accepted),
        ),
        test_case_count=2,
    )

    assert judged.verdict is Verdict.accepted


def test_the_verdict_is_the_first_test_case_result_that_did_not_pass() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(input=[], verdict=Verdict.accepted),
            TestCaseResult(input=[], verdict=Verdict.wrong_answer),
            TestCaseResult(input=[], verdict=Verdict.runtime_error),
        ),
        test_case_count=3,
    )

    assert judged.verdict is Verdict.wrong_answer


def test_a_submission_reporting_on_fewer_test_cases_than_it_was_given_is_not_accepted() -> None:
    judged = JudgedSubmission(
        test_case_results=(TestCaseResult(input=[], verdict=Verdict.accepted),),
        test_case_count=2,
    )

    assert judged.verdict is Verdict.internal_error


def test_a_submission_reporting_on_nothing_at_all_is_not_accepted() -> None:
    judged = JudgedSubmission(test_case_results=(), test_case_count=1)

    assert judged.verdict is Verdict.internal_error


def test_results_that_went_missing_with_no_limit_to_explain_them_are_a_platform_failure() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(input=[], verdict=Verdict.accepted),
            TestCaseResult(input=[], verdict=Verdict.wrong_answer),
        ),
        test_case_count=5,
    )

    assert judged.verdict is Verdict.internal_error


def test_a_submission_stopped_by_a_limit_keeps_the_first_result_that_did_not_pass() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(input=[], verdict=Verdict.wrong_answer),
            TestCaseResult(input=[], verdict=Verdict.memory_limit_exceeded),
        ),
        test_case_count=5,
    )

    assert judged.verdict is Verdict.wrong_answer


def test_a_submission_stopped_by_a_limit_is_told_so_rather_than_told_the_platform_failed() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(input=[], verdict=Verdict.accepted),
            TestCaseResult(input=[], verdict=Verdict.memory_limit_exceeded),
        ),
        test_case_count=5,
    )

    assert judged.verdict is Verdict.memory_limit_exceeded
