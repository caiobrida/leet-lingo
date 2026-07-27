from pathlib import Path

MEMORY_EVENTS = Path("/sys/fs/cgroup/memory.events")
KILL_COUNT = "oom_kill"

HOW_SOON_A_PROCESS_IS_KILLED = Path("/proc/self/oom_score_adj")
SOONER_THAN_ANYTHING_ELSE_IN_THE_SANDBOX = "1000"


def processes_the_memory_limit_has_killed() -> int:
    for line in MEMORY_EVENTS.read_text().splitlines():
        field, _, count = line.partition(" ")
        if field == KILL_COUNT:
            return int(count)
    return 0


def has_killed_a_process_since(kills: int) -> bool:
    return processes_the_memory_limit_has_killed() > kills


def be_the_first_process_the_memory_limit_kills() -> None:
    HOW_SOON_A_PROCESS_IS_KILLED.write_text(SOONER_THAN_ANYTHING_ELSE_IN_THE_SANDBOX)
