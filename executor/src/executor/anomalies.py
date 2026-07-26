import logging

OPERATOR_ANOMALIES = logging.getLogger("executor.anomalies")


def record_a_sandbox_killed_from_outside(container: str) -> None:
    OPERATOR_ANOMALIES.warning(
        "the sandbox %s outlived its own timeout and was killed from outside the container",
        container,
    )
