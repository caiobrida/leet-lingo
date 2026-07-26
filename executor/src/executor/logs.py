import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from functools import partial

SUBMISSION_ON_EVERY_LOG_LINE = "submission_id"
NO_SUBMISSION_IS_BEING_JUDGED = "-"

LOG_LINE_NAMING_THE_SUBMISSION = (
    f"%(asctime)s %(levelname)s %(name)s "
    f"submission=%({SUBMISSION_ON_EVERY_LOG_LINE})s %(message)s"
)

_the_submission_being_judged: ContextVar[str] = ContextVar(
    SUBMISSION_ON_EVERY_LOG_LINE,
    default=NO_SUBMISSION_IS_BEING_JUDGED,
)


def a_log_carrying_the_submission_being_judged(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.addFilter(_carry_the_submission_being_judged)
    return log


@contextmanager
def log_lines_carrying_the_submission(submission_id: str) -> Iterator[None]:
    carried = _the_submission_being_judged.set(submission_id)
    try:
        yield
    finally:
        _the_submission_being_judged.reset(carried)


def carrying_the_submission_into_another_thread(work: Callable[..., None]) -> Callable[..., None]:
    return partial(copy_context().run, work)


def the_executors_log_format() -> logging.Formatter:
    return logging.Formatter(
        LOG_LINE_NAMING_THE_SUBMISSION,
        defaults={SUBMISSION_ON_EVERY_LOG_LINE: NO_SUBMISSION_IS_BEING_JUDGED},
    )


def configure_the_executors_logs() -> None:
    lines = logging.StreamHandler()
    lines.setFormatter(the_executors_log_format())
    logging.basicConfig(level=logging.INFO, handlers=[lines])


def _carry_the_submission_being_judged(record: logging.LogRecord) -> bool:
    record.__dict__[SUBMISSION_ON_EVERY_LOG_LINE] = _the_submission_being_judged.get()
    return True
