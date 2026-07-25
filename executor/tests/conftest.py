import subprocess
from pathlib import Path

import pytest

from executor.sandbox import SANDBOX_IMAGE

SANDBOX_BUILD_CONTEXT = Path(__file__).resolve().parent.parent / "sandbox"


@pytest.fixture(scope="session", autouse=True)
def built_sandbox_image() -> None:
    subprocess.run(
        ["docker", "build", "--tag", SANDBOX_IMAGE, str(SANDBOX_BUILD_CONTEXT)],
        check=True,
        capture_output=True,
    )
