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
    assert judged.test_case_results == (
        TestCaseResult(verdict=Verdict.accepted, input=[2, 3], returned=5),
    )


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


def test_a_failing_test_case_reports_the_input_it_used_and_the_value_that_was_returned() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(left, right):
                return left * right
            """
        ),
        test_cases=[TestCase(input=[2, 3], expected_output=5)],
    )

    failed = judged.test_case_results[0]
    assert judged.verdict is Verdict.wrong_answer
    assert failed.input == [2, 3]
    assert failed.returned == 6


def test_every_test_case_is_judged_and_reported_in_the_order_it_was_given() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(number):
                return number * 2
            """
        ),
        test_cases=[
            TestCase(input=[1], expected_output=2),
            TestCase(input=[2], expected_output=5),
            TestCase(input=[3], expected_output=6),
        ],
    )

    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.accepted,
        Verdict.wrong_answer,
        Verdict.accepted,
    ]
    assert [result.input for result in judged.test_case_results] == [[1], [2], [3]]


def test_each_test_case_is_judged_in_its_own_freshly_spawned_child_process() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            import os

            def solve():
                return os.getpid()
            """
        ),
        test_cases=[TestCase(input=[], expected_output=None) for _ in range(3)],
    )

    assert len({result.returned for result in judged.test_case_results}) == 3


def test_state_set_while_judging_one_test_case_is_not_visible_while_judging_another() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            import sys

            def solve():
                sys.test_cases_judged_so_far = getattr(sys, "test_cases_judged_so_far", 0) + 1
                return sys.test_cases_judged_so_far
            """
        ),
        test_cases=[TestCase(input=[], expected_output=1) for _ in range(3)],
    )

    assert judged.verdict is Verdict.accepted


def test_a_solution_returning_tuples_where_lists_are_expected_is_accepted() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve():
                return (1, [2, (3, 4)])
            """
        ),
        test_cases=[TestCase(input=[], expected_output=[1, [2, [3, 4]]])],
    )

    assert judged.verdict is Verdict.accepted


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

    attempted = judge(
        solution=leave_a_marker,
        test_cases=[TestCase(input=[], expected_output="left behind")],
    )
    judged = judge(
        solution=look_for_the_marker,
        test_cases=[TestCase(input=[], expected_output=False)],
    )

    assert attempted.verdict is Verdict.runtime_error
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
