from pathlib import Path

MEMORY_EVENTS = Path("/sys/fs/cgroup/memory.events")
KILL_COUNT = "oom_kill"


def has_killed_a_process() -> bool:
    return _kills_so_far() > 0


def _kills_so_far() -> int:
    for line in MEMORY_EVENTS.read_text().splitlines():
        field, _, count = line.partition(" ")
        if field == KILL_COUNT:
            return int(count)
    return 0
