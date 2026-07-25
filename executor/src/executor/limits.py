from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    memory_bytes: int = 256 * 1024 * 1024
    cpus: float = 1.0
    processes: int = 64
