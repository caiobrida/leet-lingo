from executor.submission import JudgedSubmission, TestCaseResult, Verdict


def test_a_submission_whose_test_case_results_all_passed_is_accepted() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(verdict=Verdict.accepted),
            TestCaseResult(verdict=Verdict.accepted),
        ),
        test_case_count=2,
    )

    assert judged.verdict is Verdict.accepted


def test_the_verdict_is_the_first_test_case_result_that_did_not_pass() -> None:
    judged = JudgedSubmission(
        test_case_results=(
            TestCaseResult(verdict=Verdict.accepted),
            TestCaseResult(verdict=Verdict.wrong_answer),
            TestCaseResult(verdict=Verdict.runtime_error),
        ),
        test_case_count=3,
    )

    assert judged.verdict is Verdict.wrong_answer


def test_a_submission_reporting_on_fewer_test_cases_than_it_was_given_is_not_accepted() -> None:
    judged = JudgedSubmission(
        test_case_results=(TestCaseResult(verdict=Verdict.accepted),),
        test_case_count=2,
    )

    assert judged.verdict is Verdict.internal_error


def test_a_submission_reporting_on_nothing_at_all_is_not_accepted() -> None:
    judged = JudgedSubmission(test_case_results=(), test_case_count=1)

    assert judged.verdict is Verdict.internal_error
