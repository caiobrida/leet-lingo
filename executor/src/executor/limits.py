from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Limits:
    test_case_seconds: float = 2.0
    submission_seconds: float = 10.0
    sandbox_seconds: float = 20.0
    memory_bytes: int = 256 * 1024 * 1024
    cpus: float = 1.0
    processes: int = 64


def every_limit_named(limits: Limits) -> str:
    return " ".join(f"{limit}={bound}" for limit, bound in asdict(limits).items())
