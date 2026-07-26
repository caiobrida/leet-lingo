import subprocess
import textwrap

from executor.judging import judge
from executor.limits import Limits
from executor.sandbox import SANDBOX_IMAGE
from executor.submission import TestCase

NEVER_RETURNS = textwrap.dedent(
    """
    def solve():
        while True:
            pass
    """
)

LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT = Limits(
    test_case_seconds=120.0,
    submission_seconds=120.0,
    sandbox_seconds=3.0,
)


def test_no_container_outlives_the_submission_that_created_it() -> None:
    judge(
        solution="def solve():\n    return 1\n",
        test_cases=[TestCase(input=[], expected_output=1)],
    )

    assert _containers_made_from_the_sandbox_image() == []


def test_no_container_outlives_a_submission_killed_from_outside() -> None:
    judge(
        solution=NEVER_RETURNS,
        test_cases=[TestCase(input=[], expected_output=1)],
        limits=LONGER_INSIDE_THE_SANDBOX_THAN_OUTSIDE_IT,
    )

    assert _containers_made_from_the_sandbox_image() == []


def test_the_sandbox_image_installs_no_third_party_packages() -> None:
    installed = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "python", SANDBOX_IMAGE, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert installed.stdout.split() == []


def _containers_made_from_the_sandbox_image() -> list[str]:
    listed = subprocess.run(
        ["docker", "ps", "--all", "--quiet", "--filter", f"ancestor={SANDBOX_IMAGE}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return listed.stdout.split()
