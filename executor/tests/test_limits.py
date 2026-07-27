import textwrap
import threading
import time

from conftest import (
    A_SUBMISSION,
    ALLOCATES_WITHOUT_BOUND,
    FILLS_THE_SANDBOX_WITH_PROCESSES,
)

from executor.judging import judge
from executor.limits import Limits
from executor.submission import JudgedSubmission, TestCase, Verdict

MORE_MEMORY_THAN_THE_PROCESS_CAP_ALLOWS_A_FORK_BOMB_TO_USE = Limits(
    memory_bytes=1024 * 1024 * 1024
)

ALLOCATES_WHAT_IT_IS_ASKED_FOR = textwrap.dedent(
    """
    def solve(megabytes):
        blocks = [bytearray(1024 * 1024) for _ in range(megabytes)]
        return len(blocks)
    """
)

MEGABYTES_THE_DEFAULT_LIMIT_HAS_ROOM_FOR = 180
LESS_MEMORY_THAN_THE_SOLUTION_ASKS_FOR = Limits(memory_bytes=128 * 1024 * 1024)

WORKERS = 48
SECONDS_OF_SATURATION = 12
SECONDS_FOR_THE_SATURATION_TO_TAKE_HOLD = 3
TOLERATED_SLOWDOWN = 1.5

LONGER_THAN_THE_SATURATION_THIS_TEST_ARRANGES = Limits(
    test_case_seconds=30.0,
    submission_seconds=30.0,
    sandbox_seconds=60.0,
)

ROUNDS = 60_000_000
SUM_OF_THE_SQUARES_BELOW_ROUNDS = (ROUNDS - 1) * ROUNDS * (2 * ROUNDS - 1) // 6

ROUNDS_A_WHOLE_CPU_FINISHES_WELL_INSIDE_THE_TIMEOUT = 5_000_000
SUM_OF_THE_SQUARES_BELOW_THOSE_ROUNDS = (
    (ROUNDS_A_WHOLE_CPU_FINISHES_WELL_INSIDE_THE_TIMEOUT - 1)
    * ROUNDS_A_WHOLE_CPU_FINISHES_WELL_INSIDE_THE_TIMEOUT
    * (2 * ROUNDS_A_WHOLE_CPU_FINISHES_WELL_INSIDE_THE_TIMEOUT - 1)
    // 6
)

A_WHOLE_CPU = Limits(cpus=1.0, test_case_seconds=3.0, sandbox_seconds=60.0)
A_TENTH_OF_A_CPU = Limits(cpus=0.1, test_case_seconds=3.0, sandbox_seconds=60.0)

PROCESSES_THE_DEFAULT_CAP_HAS_ROOM_FOR = 40
FEWER_PROCESSES_THAN_THE_SOLUTION_STARTS = Limits(processes=16)

STARTS_THE_PROCESSES_IT_IS_ASKED_FOR = textwrap.dedent(
    """
    import os
    import time

    def solve(processes):
        started = []
        for _ in range(processes):
            child = os.fork()
            if child == 0:
                time.sleep(30)
                os._exit(0)
            started.append(child)
        for child in started:
            os.kill(child, 9)
            os.waitpid(child, 0)
        return len(started)
    """
)

SATURATES_THE_CPU = textwrap.dedent(
    """
    import os
    import time

    def solve(seconds, workers):
        for _ in range(workers):
            if os.fork() == 0:
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    pass
                os._exit(0)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            pass
        return workers
    """
)

WORKS_THE_CPU = textwrap.dedent(
    """
    def solve(rounds):
        total = 0
        for number in range(rounds):
            total += number * number
        return total
    """
)

ALLOCATES_WITHOUT_BOUND_ON_EVERY_TEST_CASE_BUT_THE_FIRST = textwrap.dedent(
    """
    def solve(number):
        if number == 0:
            return 0
        blocks = []
        while True:
            blocks.append(bytearray(8 * 1024 * 1024))
    """
)

STARVES_A_PROCESS_IT_STARTED_THEN_STOPS_WITHOUT_REPORTING = textwrap.dedent(
    """
    import os

    def solve(number):
        if number > 0:
            os._exit(1)
        if os.fork() == 0:
            blocks = []
            while True:
                blocks.append(bytearray(8 * 1024 * 1024))
        os.wait()
        return number
    """
)

COMPARES_HOW_SOON_IT_WOULD_BE_KILLED_TO_THE_HARNESS = textwrap.dedent(
    """
    HARNESS = 1

    def how_soon_the_memory_limit_kills(process):
        with open(f"/proc/{process}/oom_score_adj") as how_soon:
            return int(how_soon.read())

    def solve():
        return how_soon_the_memory_limit_kills("self") > how_soon_the_memory_limit_kills(HARNESS)
    """
)


def test_a_solution_allocating_without_bound_is_stopped_by_the_memory_limit() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=ALLOCATES_WITHOUT_BOUND,
        test_cases=[TestCase(input=[0], expected_output=0)],
    )

    assert judged.verdict is Verdict.memory_limit_exceeded


def test_the_test_cases_that_finished_before_the_memory_limit_are_reported_with_the_verdict() -> (
    None
):
    judged = judge(
        A_SUBMISSION,
        solution=ALLOCATES_WITHOUT_BOUND_ON_EVERY_TEST_CASE_BUT_THE_FIRST,
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(3)],
    )

    assert judged.verdict is Verdict.memory_limit_exceeded
    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.accepted,
        Verdict.memory_limit_exceeded,
    ]


def test_a_solution_stopping_without_reporting_is_not_blamed_on_an_earlier_memory_kill() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=STARVES_A_PROCESS_IT_STARTED_THEN_STOPS_WITHOUT_REPORTING,
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(2)],
    )

    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.accepted,
        Verdict.runtime_error,
    ]
    assert judged.verdict is Verdict.runtime_error


def test_the_memory_limit_kills_the_solution_before_the_harness_that_judges_it() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=COMPARES_HOW_SOON_IT_WOULD_BE_KILLED_TO_THE_HARNESS,
        test_cases=[TestCase(input=[], expected_output=True)],
    )

    assert judged.verdict is Verdict.accepted


def test_a_fork_bomb_is_contained_by_the_process_cap_rather_than_by_the_memory_limit() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=FILLS_THE_SANDBOX_WITH_PROCESSES,
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(3)],
        limits=MORE_MEMORY_THAN_THE_PROCESS_CAP_ALLOWS_A_FORK_BOMB_TO_USE,
    )

    assert judged.verdict is Verdict.runtime_error
    assert [result.verdict for result in judged.test_case_results] == [Verdict.runtime_error] * 3


def test_the_memory_limit_is_supplied_per_submission_rather_than_baked_into_the_sandbox() -> None:
    test_cases = [
        TestCase(
            input=[MEGABYTES_THE_DEFAULT_LIMIT_HAS_ROOM_FOR],
            expected_output=MEGABYTES_THE_DEFAULT_LIMIT_HAS_ROOM_FOR,
        )
    ]

    given_room = judge(A_SUBMISSION, solution=ALLOCATES_WHAT_IT_IS_ASKED_FOR, test_cases=test_cases)
    denied_room = judge(
        A_SUBMISSION,
        solution=ALLOCATES_WHAT_IT_IS_ASKED_FOR,
        test_cases=test_cases,
        limits=LESS_MEMORY_THAN_THE_SOLUTION_ASKS_FOR,
    )

    assert given_room.verdict is Verdict.accepted
    assert denied_room.verdict is Verdict.memory_limit_exceeded


def test_the_cpu_cap_is_supplied_per_submission_rather_than_baked_into_the_sandbox() -> None:
    test_cases = [
        TestCase(
            input=[ROUNDS_A_WHOLE_CPU_FINISHES_WELL_INSIDE_THE_TIMEOUT],
            expected_output=SUM_OF_THE_SQUARES_BELOW_THOSE_ROUNDS,
        )
    ]

    given_a_whole_cpu = judge(
        A_SUBMISSION, solution=WORKS_THE_CPU, test_cases=test_cases, limits=A_WHOLE_CPU
    )
    given_a_tenth_of_one = judge(
        A_SUBMISSION, solution=WORKS_THE_CPU, test_cases=test_cases, limits=A_TENTH_OF_A_CPU
    )

    assert given_a_whole_cpu.verdict is Verdict.accepted
    assert given_a_tenth_of_one.verdict is Verdict.time_limit_exceeded


def test_the_process_cap_is_supplied_per_submission_rather_than_baked_into_the_sandbox() -> None:
    test_cases = [
        TestCase(
            input=[PROCESSES_THE_DEFAULT_CAP_HAS_ROOM_FOR],
            expected_output=PROCESSES_THE_DEFAULT_CAP_HAS_ROOM_FOR,
        )
    ]

    given_room = judge(
        A_SUBMISSION, solution=STARTS_THE_PROCESSES_IT_IS_ASKED_FOR, test_cases=test_cases
    )
    denied_room = judge(
        A_SUBMISSION,
        solution=STARTS_THE_PROCESSES_IT_IS_ASKED_FOR,
        test_cases=test_cases,
        limits=FEWER_PROCESSES_THAN_THE_SOLUTION_STARTS,
    )

    assert given_room.verdict is Verdict.accepted
    assert denied_room.verdict is Verdict.runtime_error


def test_a_solution_saturating_the_cpu_does_not_slow_a_submission_judged_alongside_it() -> None:
    saturated: list[JudgedSubmission] = []
    seconds_alone, judged_alone = _judge_a_submission_that_works_the_cpu()

    saturating = threading.Thread(
        target=lambda: saturated.append(_judge_a_solution_saturating_every_cpu_it_can_reach())
    )
    saturating.start()
    time.sleep(SECONDS_FOR_THE_SATURATION_TO_TAKE_HOLD)
    seconds_alongside, judged_alongside = _judge_a_submission_that_works_the_cpu()
    saturating.join()

    assert [judged.verdict for judged in saturated] == [Verdict.accepted]
    assert judged_alone.verdict is Verdict.accepted
    assert judged_alongside.verdict is Verdict.accepted
    assert seconds_alongside < seconds_alone * TOLERATED_SLOWDOWN


def _judge_a_submission_that_works_the_cpu() -> tuple[float, JudgedSubmission]:
    started = time.monotonic()
    judged = judge(
        A_SUBMISSION,
        solution=WORKS_THE_CPU,
        test_cases=[TestCase(input=[ROUNDS], expected_output=SUM_OF_THE_SQUARES_BELOW_ROUNDS)],
        limits=LONGER_THAN_THE_SATURATION_THIS_TEST_ARRANGES,
    )
    return time.monotonic() - started, judged


def _judge_a_solution_saturating_every_cpu_it_can_reach() -> JudgedSubmission:
    return judge(
        A_SUBMISSION,
        solution=SATURATES_THE_CPU,
        test_cases=[TestCase(input=[SECONDS_OF_SATURATION, WORKERS], expected_output=WORKERS)],
        limits=LONGER_THAN_THE_SATURATION_THIS_TEST_ARRANGES,
    )
