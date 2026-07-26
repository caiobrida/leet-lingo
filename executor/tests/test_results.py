from executor.results import read_test_case_results
from executor.submission import TestCase, Verdict

A_STREAM_CUT_OFF_MID_LINE = (
    '{"verdict": "accepted", "returned": 0, "printed_output": ""}\n'
    '{"verdict": "accepted", "returned": 1, "printed_output": ""}\n'
    '{"verdict": "accep'
)

THREE_TEST_CASES = [TestCase(input=[number], expected_output=number) for number in range(3)]


def test_a_stream_cut_off_mid_line_yields_the_results_that_preceded_it() -> None:
    results = read_test_case_results(A_STREAM_CUT_OFF_MID_LINE, THREE_TEST_CASES)

    assert [result.verdict for result in results] == [Verdict.accepted] * 2
    assert [result.returned for result in results] == [0, 1]
