import os
import signal
import time

SECONDS_BETWEEN_SWEEPS = 0.01


def start_a_new_process_group() -> None:
    os.setsid()


def kill_the_process_group(leader: int) -> None:
    while _killed_whoever_is_left(leader):
        _reap_whoever_has_died()
        time.sleep(SECONDS_BETWEEN_SWEEPS)


def _killed_whoever_is_left(leader: int) -> bool:
    try:
        os.killpg(leader, signal.SIGKILL)
    except ProcessLookupError:
        return False
    return True


def _reap_whoever_has_died() -> None:
    while _reaped_one():
        pass


def _reaped_one() -> bool:
    try:
        reaped, _ = os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        return False
    return reaped != 0
