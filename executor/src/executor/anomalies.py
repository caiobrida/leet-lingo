import logging

OPERATOR_ANOMALIES = logging.getLogger("executor.anomalies")


def record_a_sandbox_killed_from_outside(container: str) -> None:
    OPERATOR_ANOMALIES.warning(
        "the sandbox %s stopped enforcing its own timeouts and had to be killed from outside",
        container,
    )
