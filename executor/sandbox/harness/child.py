import json
from multiprocessing.connection import Connection
from typing import Any

ENTRY_POINT = "solve"


def run_solution(solution: str, test_case_input: list[Any], returned_values: Connection) -> None:
    namespace: dict[str, Any] = {}
    exec(compile(solution, "<solution>", "exec"), namespace)
    returned = namespace[ENTRY_POINT](*test_case_input)
    returned_values.send_bytes(json.dumps(returned).encode())
    returned_values.close()
