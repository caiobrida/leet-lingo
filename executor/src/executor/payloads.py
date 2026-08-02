from pydantic import BaseModel, Field

from executor.limits import Limits
from executor.submission import JudgedSubmission, TestCase, TestCaseResult, Verdict

AT_LEAST_ONE_TEST_CASE_TO_JUDGE_AGAINST = Field(min_length=1)


class SubmissionToJudge(BaseModel):
    submission_id: str
    solution: str
    test_cases: list[TestCase] = AT_LEAST_ONE_TEST_CASE_TO_JUDGE_AGAINST
    limits: Limits


class AnsweredToTheCaller(BaseModel):
    verdict: Verdict
    test_case_results: list[TestCaseResult]


def the_answer_a_caller_receives(judged: JudgedSubmission) -> AnsweredToTheCaller:
    return AnsweredToTheCaller(
        verdict=judged.verdict,
        test_case_results=list(judged.test_case_results),
    )
