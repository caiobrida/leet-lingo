import json
import multiprocessing
from collections.abc import Iterator
from typing import Any

from harness.child import run_solution
from harness.payload import TestCase

ACCEPTED = "accepted"
WRONG_ANSWER = "wrong_answer"


def judge_test_cases(solution: str, test_cases: list[TestCase]) -> Iterator[dict[str, Any]]:
    for test_case in test_cases:
        returned = _run_in_child_process(solution, test_case.input)
        yield {"verdict": ACCEPTED if returned == test_case.expected_output else WRONG_ANSWER}


def _run_in_child_process(solution: str, test_case_input: list[Any]) -> Any:
    returned_values, sent_by_the_child = multiprocessing.Pipe(duplex=False)
    child = multiprocessing.Process(
        target=run_solution,
        args=(solution, test_case_input, sent_by_the_child),
    )
    child.start()
    sent_by_the_child.close()
    try:
        return json.loads(returned_values.recv_bytes())
    finally:
        returned_values.close()
        child.join()
