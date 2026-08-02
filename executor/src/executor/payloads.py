from pydantic import BaseModel

from executor.limits import Limits
from executor.submission import JudgedSubmission, TestCase, TestCaseResult, Verdict


class SubmissionToJudge(BaseModel):
    submission_id: str
    solution: str
    test_cases: list[TestCase]
    limits: Limits = Limits()


class JudgedSubmissionAnswered(BaseModel):
    verdict: Verdict
    test_case_results: list[TestCaseResult]


def the_answer_a_caller_receives(judged: JudgedSubmission) -> JudgedSubmissionAnswered:
    return JudgedSubmissionAnswered(
        verdict=judged.verdict,
        test_case_results=list(judged.test_case_results),
    )
