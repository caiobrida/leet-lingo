import os
import pwd
import signal
import time
from collections.abc import Iterator

from harness.privileges import SOLUTION_ACCOUNT

SECONDS_BETWEEN_SWEEPS = 0.01


def kill_everything_the_solution_started() -> None:
    owned_by_the_solution = pwd.getpwnam(SOLUTION_ACCOUNT).pw_uid
    while _killed_whoever_is_left(owned_by_the_solution):
        _reap_whoever_has_died()
        time.sleep(SECONDS_BETWEEN_SWEEPS)


def _killed_whoever_is_left(owned_by_the_solution: int) -> bool:
    still_there = False
    for process in _processes_owned_by(owned_by_the_solution):
        try:
            os.kill(process, signal.SIGKILL)
        except ProcessLookupError:
            continue
        still_there = True
    return still_there


def _processes_owned_by(owner: int) -> Iterator[int]:
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            if os.stat(f"/proc/{entry}").st_uid == owner:
                yield int(entry)
        except OSError:
            continue


def _reap_whoever_has_died() -> None:
    while _reaped_one():
        pass


def _reaped_one() -> bool:
    try:
        reaped, _ = os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        return False
    return reaped != 0
