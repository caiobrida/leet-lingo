import textwrap

from conftest import A_SUBMISSION

from executor.judging import judge
from executor.submission import TestCase, Verdict

OPENS_A_NETWORK_CONNECTION = textwrap.dedent(
    """
    import socket

    def solve(host, port):
        socket.create_connection((host, port), timeout=5)
        return "reached the network"
    """
)

A_HOST_OUTSIDE_THE_SANDBOX = ["1.1.1.1", 53]

WRITES_TO_A_PATH = textwrap.dedent(
    """
    def solve(path):
        with open(path, "w") as written:
            written.write("left behind")
        return "wrote to the filesystem"
    """
)

PLACES_A_SOLUTION_MIGHT_TRY_TO_WRITE = [
    "/leet-lingo",
    "/tmp/leet-lingo",
    "/var/tmp/leet-lingo",
    "/home/leet-lingo",
    "/run/leet-lingo",
    "/dev/leet-lingo",
    "/dev/shm/leet-lingo",
]

THE_SOURCE_OF_THE_HARNESS_THAT_JUDGES = "/opt/harness/judging.py"

BECOMES_A_PRIVILEGED_USER = textwrap.dedent(
    """
    import os

    def solve():
        os.setuid(0)
        return "became a privileged user"
    """
)

READS_A_PATH = textwrap.dedent(
    """
    def solve(path):
        with open(path) as protected:
            return protected.read()
    """
)

A_FILE_ONLY_A_PRIVILEGED_USER_CAN_READ = "/etc/shadow"

LOOKS_FOR_A_BINARY_THAT_WOULD_GRANT_IT_PRIVILEGES = textwrap.dedent(
    """
    import os
    import stat

    GRANTS_THE_PRIVILEGES_OF_ITS_OWNER = stat.S_ISUID | stat.S_ISGID

    def solve(directories):
        for directory in directories:
            for visited, _, names in os.walk(directory, onerror=lambda refused: None):
                for name in names:
                    path = os.path.join(visited, name)
                    try:
                        mode = os.lstat(path).st_mode
                    except OSError:
                        continue
                    if mode & GRANTS_THE_PRIVILEGES_OF_ITS_OWNER:
                        return path
        return "nothing to escalate to"
    """
)

EVERY_DIRECTORY_THE_SANDBOX_KEEPS_EXECUTABLES_IN = ["/usr", "/opt", "/etc", "/var"]

COMPARES_ITS_USER_TO_THE_USER_THE_HARNESS_RUNS_UNDER = textwrap.dedent(
    """
    import os

    HARNESS = 1
    REAL_USER = 1

    def solve():
        for line in open(f"/proc/{HARNESS}/status"):
            if line.startswith("Uid:"):
                return os.getuid() == int(line.split()[REAL_USER])
        return "the harness reports no user"
    """
)

KILLS_THE_HARNESS_THAT_JUDGES_IT = textwrap.dedent(
    """
    import os
    import signal

    HARNESS = 1

    def solve(number):
        os.kill(HARNESS, signal.SIGKILL)
        return number
    """
)

A_PREFIX_OF_THE_EXPECTED_OUTPUT = "leet-lingo-expected-output-"
CHARACTERS_OF_THE_EXPECTED_OUTPUT_ONLY_THE_HARNESS_HOLDS = 4
AN_EXPECTED_OUTPUT_ONLY_THE_HARNESS_HOLDS = f"{A_PREFIX_OF_THE_EXPECTED_OUTPUT}8c21"

SEARCHES_THE_HARNESS_MEMORY_FOR_THE_EXPECTED_OUTPUT = textwrap.dedent(
    """
    import os

    HARNESS = 1
    LARGEST_REGION_WORTH_READING = 64 * 1024 * 1024

    def regions_the_harness_keeps_its_objects_in():
        with open(f"/proc/{HARNESS}/maps") as maps:
            for line in maps:
                fields = line.split()
                bounds, permissions = fields[0], fields[1]
                backed_by_a_file = len(fields) > 5 and fields[5].startswith("/")
                low, _, high = bounds.partition("-")
                low, high = int(low, 16), int(high, 16)
                readable = permissions.startswith("r")
                if readable and not backed_by_a_file:
                    if high - low <= LARGEST_REGION_WORTH_READING:
                        yield low, high

    def solve(prefix, remaining):
        wanted = prefix.encode()
        memory = os.open(f"/proc/{HARNESS}/mem", os.O_RDONLY)
        for low, high in regions_the_harness_keeps_its_objects_in():
            try:
                block = os.pread(memory, high - low, low)
            except OSError:
                continue
            found = block.find(wanted)
            if found != -1:
                return block[found : found + len(wanted) + remaining].decode()
        return "out of reach"
    """
)


def test_a_solution_opening_a_network_connection_fails_inside_the_sandbox() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=OPENS_A_NETWORK_CONNECTION,
        test_cases=[
            TestCase(input=A_HOST_OUTSIDE_THE_SANDBOX, expected_output="reached the network")
        ],
    )

    refused = judged.test_case_results[0]
    assert judged.verdict is Verdict.runtime_error
    assert refused.error is not None
    assert "Network is unreachable" in refused.error


def test_a_solution_writing_to_the_filesystem_fails_wherever_it_tries() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=WRITES_TO_A_PATH,
        test_cases=[
            TestCase(input=[path], expected_output="wrote to the filesystem")
            for path in PLACES_A_SOLUTION_MIGHT_TRY_TO_WRITE
        ],
    )

    assert [result.verdict for result in judged.test_case_results] == [Verdict.runtime_error] * len(
        PLACES_A_SOLUTION_MIGHT_TRY_TO_WRITE
    )


def test_a_solution_cannot_overwrite_the_harness_that_judges_it() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=WRITES_TO_A_PATH,
        test_cases=[
            TestCase(
                input=[THE_SOURCE_OF_THE_HARNESS_THAT_JUDGES],
                expected_output="wrote to the filesystem",
            )
        ],
    )

    assert judged.verdict is Verdict.runtime_error


def test_a_solution_cannot_become_a_privileged_user() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=BECOMES_A_PRIVILEGED_USER,
        test_cases=[TestCase(input=[], expected_output="became a privileged user")],
    )

    refused = judged.test_case_results[0]
    assert judged.verdict is Verdict.runtime_error
    assert refused.error is not None
    assert "PermissionError" in refused.error


def test_a_solution_cannot_read_a_file_only_a_privileged_user_could_read() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=READS_A_PATH,
        test_cases=[TestCase(input=[A_FILE_ONLY_A_PRIVILEGED_USER_CAN_READ], expected_output="")],
    )

    refused = judged.test_case_results[0]
    assert judged.verdict is Verdict.runtime_error
    assert refused.error is not None
    assert "PermissionError" in refused.error


def test_a_solution_finds_no_binary_in_the_sandbox_that_would_grant_it_privileges() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=LOOKS_FOR_A_BINARY_THAT_WOULD_GRANT_IT_PRIVILEGES,
        test_cases=[
            TestCase(
                input=[EVERY_DIRECTORY_THE_SANDBOX_KEEPS_EXECUTABLES_IN],
                expected_output="nothing to escalate to",
            )
        ],
    )

    assert judged.verdict is Verdict.accepted


def test_a_solution_runs_under_a_different_user_from_the_harness_that_judges_it() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=COMPARES_ITS_USER_TO_THE_USER_THE_HARNESS_RUNS_UNDER,
        test_cases=[TestCase(input=[], expected_output=False)],
    )

    assert judged.verdict is Verdict.accepted


def test_a_solution_cannot_signal_the_harness_that_judges_it() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=KILLS_THE_HARNESS_THAT_JUDGES_IT,
        test_cases=[TestCase(input=[number], expected_output=number) for number in range(3)],
    )

    assert [result.verdict for result in judged.test_case_results] == [Verdict.runtime_error] * 3


def test_a_solution_cannot_read_the_expected_output_out_of_the_harness_memory() -> None:
    judged = judge(
        A_SUBMISSION,
        solution=SEARCHES_THE_HARNESS_MEMORY_FOR_THE_EXPECTED_OUTPUT,
        test_cases=[
            TestCase(
                input=[
                    A_PREFIX_OF_THE_EXPECTED_OUTPUT,
                    CHARACTERS_OF_THE_EXPECTED_OUTPUT_ONLY_THE_HARNESS_HOLDS,
                ],
                expected_output=AN_EXPECTED_OUTPUT_ONLY_THE_HARNESS_HOLDS,
            )
        ],
    )

    assert judged.verdict is not Verdict.accepted
