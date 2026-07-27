from executor.logs import a_log_carrying_the_submission_being_judged

OPERATOR_ANOMALIES = a_log_carrying_the_submission_being_judged("executor.anomalies")


def record_a_sandbox_killed_from_outside(container: str) -> None:
    OPERATOR_ANOMALIES.warning(
        "the sandbox %s stopped enforcing its own timeouts and had to be killed from outside",
        container,
    )
