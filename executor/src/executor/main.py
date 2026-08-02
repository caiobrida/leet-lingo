from fastapi import FastAPI, Response
from fastapi.concurrency import run_in_threadpool

from executor.judging import judge
from executor.logs import configure_the_executors_logs
from executor.metrics import THE_FORMAT_A_SCRAPE_IS_READ_IN, the_metrics_an_operator_scrapes
from executor.payloads import (
    JudgedSubmissionAnswered,
    SubmissionToJudge,
    the_answer_a_caller_receives,
)

configure_the_executors_logs()

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(
        content=the_metrics_an_operator_scrapes(),
        media_type=THE_FORMAT_A_SCRAPE_IS_READ_IN,
    )


@app.post("/submissions")
async def judge_a_submission(sent: SubmissionToJudge) -> JudgedSubmissionAnswered:
    judged = await run_in_threadpool(
        judge,
        sent.submission_id,
        sent.solution,
        sent.test_cases,
        sent.limits,
    )
    return the_answer_a_caller_receives(judged)
