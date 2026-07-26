from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from executor.submission import Verdict

THE_DIMENSION_A_VERDICT_IS_COUNTED_ON = "verdict"

THE_FORMAT_A_SCRAPE_IS_READ_IN = CONTENT_TYPE_LATEST

WHAT_THE_COUNT_MEANS_TO_AN_OPERATOR = (
    "Submissions judged, counted under the verdict each was given."
)

SUBMISSIONS_JUDGED = Counter(
    "submissions_judged",
    WHAT_THE_COUNT_MEANS_TO_AN_OPERATOR,
    [THE_DIMENSION_A_VERDICT_IS_COUNTED_ON],
)


def count_the_verdict(verdict: Verdict) -> None:
    SUBMISSIONS_JUDGED.labels(**{THE_DIMENSION_A_VERDICT_IS_COUNTED_ON: verdict.value}).inc()


def the_metrics_an_operator_scrapes() -> bytes:
    return generate_latest()
