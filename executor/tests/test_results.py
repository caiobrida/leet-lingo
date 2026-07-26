from executor.results import read_test_case_results
from executor.submission import TestCase, Verdict

A_RESULT_FOR_EVERY_TEST_CASE = (
    '{"verdict": "accepted", "returned": 0, "printed_output": ""}\n'
    '{"verdict": "accepted", "returned": 1, "printed_output": ""}\n'
    '{"verdict": "accepted", "returned": 2, "printed_output": ""}\n'
)

A_STREAM_CUT_OFF_MID_LINE = (
    '{"verdict": "accepted", "returned": 0, "printed_output": ""}\n'
    '{"verdict": "accepted", "returned": 1, "printed_output": ""}\n'
    '{"verdict": "accep'
)

A_STREAM_CARRYING_A_VERDICT_THAT_DOES_NOT_EXIST = (
    '{"verdict": "accepted", "returned": 0, "printed_output": ""}\n'
    '{"verdict": "brilliant", "returned": 1, "printed_output": ""}\n'
)

A_STREAM_CARRYING_SOMETHING_OTHER_THAN_A_RESULT = (
    '{"verdict": "accepted", "returned": 0, "printed_output": ""}\n["not a result"]\n'
)

THREE_TEST_CASES = [TestCase(input=[number], expected_output=number) for number in range(3)]


def test_every_line_of_a_complete_stream_becomes_a_test_case_result() -> None:
    results = read_test_case_results(A_RESULT_FOR_EVERY_TEST_CASE, THREE_TEST_CASES)

    assert [result.verdict for result in results] == [Verdict.accepted] * 3
    assert [result.input for result in results] == [[0], [1], [2]]


def test_a_stream_cut_off_mid_line_yields_the_results_that_preceded_it() -> None:
    results = read_test_case_results(A_STREAM_CUT_OFF_MID_LINE, THREE_TEST_CASES)

    assert [result.returned for result in results] == [0, 1]


def test_a_line_carrying_a_verdict_that_does_not_exist_ends_the_results() -> None:
    results = read_test_case_results(
        A_STREAM_CARRYING_A_VERDICT_THAT_DOES_NOT_EXIST, THREE_TEST_CASES
    )

    assert [result.returned for result in results] == [0]


def test_a_line_carrying_something_other_than_a_result_ends_the_results() -> None:
    results = read_test_case_results(
        A_STREAM_CARRYING_SOMETHING_OTHER_THAN_A_RESULT, THREE_TEST_CASES
    )

    assert [result.returned for result in results] == [0]
