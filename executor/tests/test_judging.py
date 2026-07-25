import textwrap

from executor.judging import judge
from executor.submission import TestCase, TestCaseResult, Verdict


def test_a_solution_satisfying_its_single_test_case_is_accepted() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(left, right):
                return left + right
            """
        ),
        test_cases=[TestCase(input=[2, 3], expected_output=5)],
    )

    assert judged.verdict is Verdict.accepted
    assert judged.test_case_results == (TestCaseResult(verdict=Verdict.accepted),)


def test_a_solution_returning_something_else_than_the_expected_output_is_not_accepted() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(left, right):
                return left * right
            """
        ),
        test_cases=[TestCase(input=[2, 3], expected_output=5)],
    )

    assert judged.verdict is not Verdict.accepted


def test_each_submission_is_judged_in_a_sandbox_carrying_nothing_from_the_last_one() -> None:
    marker = "/tmp/leet-lingo-marker"
    leave_a_marker = textwrap.dedent(
        f"""
        def solve():
            open({marker!r}, "w").close()
            return "left behind"
        """
    )
    look_for_the_marker = textwrap.dedent(
        f"""
        import os

        def solve():
            return os.path.exists({marker!r})
        """
    )

    judge(
        solution=leave_a_marker,
        test_cases=[TestCase(input=[], expected_output="left behind")],
    )
    judged = judge(
        solution=look_for_the_marker,
        test_cases=[TestCase(input=[], expected_output=False)],
    )

    assert judged.verdict is Verdict.accepted


def test_the_solution_runs_in_a_child_process_started_with_spawn() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            import multiprocessing

            def solve():
                return multiprocessing.get_start_method()
            """
        ),
        test_cases=[TestCase(input=[], expected_output="spawn")],
    )

    assert judged.verdict is Verdict.accepted


def test_the_expected_output_cannot_be_found_in_the_memory_of_the_child_process() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            import gc

            def solve():
                needle = "leet-lingo-expected-output-"
                for tracked in gc.get_objects():
                    for referent in gc.get_referents(tracked):
                        found = isinstance(referent, str) and referent.startswith(needle)
                        if found and referent != needle:
                            return referent
                return "out of reach"
            """
        ),
        test_cases=[TestCase(input=[], expected_output="leet-lingo-expected-output-3f9a")],
    )

    assert judged.verdict is not Verdict.accepted


def test_a_submission_larger_than_the_pipe_buffer_is_judged_without_deadlocking() -> None:
    numbers = list(range(200_000))

    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(numbers):
                return sum(numbers)
            """
        ),
        test_cases=[TestCase(input=[numbers], expected_output=sum(numbers))],
    )

    assert judged.verdict is Verdict.accepted
