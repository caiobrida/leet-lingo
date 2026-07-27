from fastapi import FastAPI, Response

from executor.logs import configure_the_executors_logs
from executor.metrics import THE_FORMAT_A_SCRAPE_IS_READ_IN, the_metrics_an_operator_scrapes

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
