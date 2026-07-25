import json
import multiprocessing
import sys

from harness.judging import judge_test_cases
from harness.payload import parse_payload


def main() -> None:
    multiprocessing.set_start_method("spawn")
    payload = parse_payload(sys.stdin.read())
    for result in judge_test_cases(payload.solution, payload.test_cases):
        sys.stdout.write(json.dumps(result) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
