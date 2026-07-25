import textwrap

from executor.judging import judge
from executor.submission import TestCase, Verdict


def test_a_solution_raising_an_exception_names_it_and_the_test_case_it_happened_on() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(divisor):
                return 10 // divisor
            """
        ),
        test_cases=[
            TestCase(input=[5], expected_output=2),
            TestCase(input=[0], expected_output=0),
        ],
    )

    raised = judged.test_case_results[1]
    assert judged.verdict is Verdict.runtime_error
    assert judged.test_case_results[0].verdict is Verdict.accepted
    assert raised.verdict is Verdict.runtime_error
    assert raised.input == [0]
    assert raised.error is not None
    assert "ZeroDivisionError" in raised.error


def test_a_solution_with_a_syntax_error_reads_as_a_mistake_the_learner_can_fix() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve():
                return (1, 2
            """
        ),
        test_cases=[TestCase(input=[], expected_output=[1, 2])],
    )

    failed = judged.test_case_results[0]
    assert judged.verdict is Verdict.runtime_error
    assert failed.error is not None
    assert "SyntaxError" in failed.error
    assert "line 3" in failed.error
    assert "return (1, 2" in failed.error


def test_a_solution_defining_no_entry_point_is_told_which_name_was_expected() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def sovle(number):
                return number
            """
        ),
        test_cases=[TestCase(input=[1], expected_output=1)],
    )

    failed = judged.test_case_results[0]
    assert judged.verdict is Verdict.runtime_error
    assert failed.error is not None
    assert "solve" in failed.error
    assert "KeyError" not in failed.error
    assert "Traceback" not in failed.error


def test_a_solution_returning_a_value_that_cannot_be_reported_says_so_and_keeps_its_output() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            def solve(numbers):
                print("about to return a set")
                return set(numbers)
            """
        ),
        test_cases=[TestCase(input=[[1, 2]], expected_output=[1, 2])],
    )

    failed = judged.test_case_results[0]
    assert failed.verdict is Verdict.runtime_error
    assert failed.error is not None
    assert "set" in failed.error
    assert failed.printed_output == "about to return a set\n"


def test_a_solution_exiting_on_an_early_test_case_leaves_the_rest_still_judged() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            import sys

            def solve(number):
                if number == 0:
                    sys.exit(1)
                return number
            """
        ),
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(3)],
    )

    assert [result.verdict for result in judged.test_case_results] == [
        Verdict.runtime_error,
        Verdict.accepted,
        Verdict.accepted,
    ]


def test_a_solution_killing_its_process_on_an_early_test_case_leaves_the_rest_still_judged() -> None:
    judged = judge(
        solution=textwrap.dedent(
            """
            import os

            def solve(number):
                if number == 0:
                    os._exit(0)
                return number
            """
        ),
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(3)],
    )

    killed = judged.test_case_results[0]
    assert killed.verdict is Verdict.runtime_error
    assert killed.error is not None
    assert [result.verdict for result in judged.test_case_results[1:]] == [
        Verdict.accepted,
        Verdict.accepted,
    ]
