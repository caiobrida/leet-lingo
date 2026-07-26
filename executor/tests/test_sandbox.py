import subprocess

from conftest import (
    SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
    WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
)

from executor.judging import judge
from executor.sandbox import SANDBOX_IMAGE
from executor.submission import TestCase

WEDGES_ON_ITS_ONLY_TEST_CASE = 0


def test_no_container_outlives_the_submission_that_created_it() -> None:
    judge(
        solution="def solve():\n    return 1\n",
        test_cases=[TestCase(input=[], expected_output=1)],
    )

    assert _containers_made_from_the_sandbox_image() == []


def test_no_container_outlives_a_submission_killed_from_outside() -> None:
    judge(
        solution=WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH,
        test_cases=[TestCase(input=[0, WEDGES_ON_ITS_ONLY_TEST_CASE], expected_output=0)],
        limits=SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP,
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
