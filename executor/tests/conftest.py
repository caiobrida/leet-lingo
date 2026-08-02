import subprocess
import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from executor.limits import Limits
from executor.main import app
from executor.sandbox import A_NAME_ONLY_OUR_CONTAINERS_CARRY, SANDBOX_IMAGE

SANDBOX_BUILD_CONTEXT = Path(__file__).resolve().parent.parent / "sandbox"

A_SUBMISSION = "submission-under-test"

AN_IMAGE_THE_HOST_WAS_NEVER_GIVEN = "leet-lingo-sandbox-that-was-never-built:latest"

RETURNS_ITS_ARGUMENT = textwrap.dedent(
    """
    def solve(number):
        return number
    """
)

WEDGES_THE_HARNESS_WAITING_FOR_A_REPORT_IT_WILL_NEVER_FINISH = textwrap.dedent(
    """
    import os
    import struct

    MORE_BYTES_THAN_THE_SOLUTION_WILL_EVER_SEND = 1024 * 1024
    THE_STREAMS_EVERY_PROCESS_STARTS_WITH = 3

    def solve(number, wedge_from):
        if number < wedge_from:
            return number
        promise = struct.pack("!i", MORE_BYTES_THAN_THE_SOLUTION_WILL_EVER_SEND)
        for name in os.listdir("/proc/self/fd"):
            descriptor = int(name)
            if descriptor >= THE_STREAMS_EVERY_PROCESS_STARTS_WITH:
                try:
                    os.write(descriptor, promise)
                except OSError:
                    pass
        while True:
            pass
    """
)

FILLS_THE_SANDBOX_WITH_PROCESSES = textwrap.dedent(
    """
    import os

    def solve(number):
        while True:
            os.fork()
        return number
    """
)

ALLOCATES_WITHOUT_BOUND = textwrap.dedent(
    """
    def solve(number):
        blocks = []
        while True:
            blocks.append(bytearray(8 * 1024 * 1024))
    """
)

SOONER_THAN_THE_HARNESS_WOULD_HAVE_GIVEN_UP = Limits(sandbox_seconds=5.0)


@pytest.fixture(scope="session", autouse=True)
def built_sandbox_image() -> None:
    subprocess.run(
        ["docker", "build", "--tag", SANDBOX_IMAGE, str(SANDBOX_BUILD_CONTEXT)],
        check=True,
        capture_output=True,
    )


@pytest.fixture
def executor() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


def containers_still_on_the_host() -> list[str]:
    listed = subprocess.run(
        [
            "docker",
            "ps",
            "--all",
            "--quiet",
            "--filter",
            f"name={A_NAME_ONLY_OUR_CONTAINERS_CARRY}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return listed.stdout.split()
