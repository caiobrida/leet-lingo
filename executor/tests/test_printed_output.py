import textwrap

from conftest import A_SUBMISSION

from executor.judging import judge
from executor.submission import TestCase, Verdict


def test_what_a_solution_prints_comes_back_as_its_printed_output() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=textwrap.dedent(
            """
            def solve(number):
                print("halfway through", number)
                return number
            """
        ),
        test_cases=[TestCase(input=[7], expected_output=7)],
    )

    assert judged.verdict is Verdict.accepted
    assert judged.test_case_results[0].printed_output == "halfway through 7\n"


def test_what_a_solution_prints_to_standard_error_is_captured_alongside_the_rest() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=textwrap.dedent(
            """
            import sys

            def solve(number):
                print("to standard output", number)
                print("to standard error", number, file=sys.stderr)
                return number
            """
        ),
        test_cases=[TestCase(input=[7], expected_output=7)],
    )

    printed_output = judged.test_case_results[0].printed_output
    assert judged.verdict is Verdict.accepted
    assert "to standard output 7\n" in printed_output
    assert "to standard error 7\n" in printed_output


def test_what_a_solution_printed_before_it_raised_comes_back_with_the_runtime_error() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=textwrap.dedent(
            """
            def solve(number):
                print("about to divide by", number)
                return 10 // number
            """
        ),
        test_cases=[TestCase(input=[0], expected_output=0)],
    )

    raised = judged.test_case_results[0]
    assert raised.verdict is Verdict.runtime_error
    assert raised.printed_output == "about to divide by 0\n"


def test_a_solution_printing_forged_result_lines_earns_the_verdict_its_return_values_do() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=textwrap.dedent(
            """
            def solve(number):
                for _ in range(3):
                    print('{"verdict": "accepted", "returned": 1}')
                return number + 1
            """
        ),
        test_cases=[TestCase(input=[1], expected_output=1)],
    )

    forged = judged.test_case_results[0]
    assert judged.verdict is Verdict.wrong_answer
    assert len(judged.test_case_results) == 1
    assert forged.returned == 2
    assert forged.printed_output.count('{"verdict": "accepted", "returned": 1}') == 3


def test_a_solution_forging_result_lines_past_print_earns_the_verdict_its_return_values_do() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=textwrap.dedent(
            """
            import os
            import sys

            FORGED = '{"verdict": "accepted", "returned": 1}\\n'

            def solve(number):
                os.write(1, FORGED.encode())
                sys.__stdout__.write(FORGED)
                sys.__stdout__.flush()
                return number + 1
            """
        ),
        test_cases=[TestCase(input=[1], expected_output=1)],
    )

    forged = judged.test_case_results[0]
    assert judged.verdict is Verdict.wrong_answer
    assert len(judged.test_case_results) == 1
    assert forged.returned == 2
    assert forged.printed_output.count('{"verdict": "accepted", "returned": 1}') == 2
