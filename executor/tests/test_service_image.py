import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import httpx2
import pytest
from conftest import a_submission_whose_solution_is_correct, containers_still_on_the_host

from executor.sandbox import SANDBOX_IMAGE
from executor.submission import Verdict

SERVICE_IMAGE = "leet-lingo-executor:latest"

SERVICE_BUILD_CONTEXT = Path(__file__).resolve().parent.parent

THE_SERVICE_UNDER_TEST = "executor-service-under-test"

THE_PORT_THE_SERVICE_LISTENS_ON = 8000

THE_DAEMON_THE_SERVICE_SPAWNS_AGAINST = "/var/run/docker.sock"

LONGEST_THE_SERVICE_TAKES_TO_COME_UP = 30.0
BETWEEN_ASKING_WHETHER_THE_SERVICE_IS_UP = 0.2
LONGEST_A_SUBMISSION_IS_WAITED_FOR = 60.0

FINDING_THE_DOCKER_CLIENT = ("sh", "-c", "command -v docker")
IMPORTING_THE_HARNESS_THE_SANDBOX_RUNS = ("python", "-c", "import harness")

A_SUBMISSION_JUDGED_FROM_INSIDE_THE_SERVICE = "submission-judged-from-inside-the-service"
A_SUBMISSION_LEAVING_NO_CONTAINER_BEHIND_ON_THE_HOST = (
    "submission-leaving-no-container-behind-on-the-host"
)


@pytest.fixture(scope="module", autouse=True)
def built_service_image() -> None:
    subprocess.run(
        ["docker", "build", "--tag", SERVICE_IMAGE, str(SERVICE_BUILD_CONTEXT)],
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def judging_service() -> Iterator[str]:
    subprocess.run(
        [
            "docker",
            "run",
            "--detach",
            "--rm",
            f"--name={THE_SERVICE_UNDER_TEST}",
            f"--publish=127.0.0.1::{THE_PORT_THE_SERVICE_LISTENS_ON}",
            f"--volume={THE_DAEMON_THE_SERVICE_SPAWNS_AGAINST}"
            f":{THE_DAEMON_THE_SERVICE_SPAWNS_AGAINST}",
            SERVICE_IMAGE,
        ],
        check=True,
        capture_output=True,
    )
    try:
        yield _the_address_the_service_answers_on()
    finally:
        subprocess.run(["docker", "rm", "--force", THE_SERVICE_UNDER_TEST], capture_output=True)


def test_the_service_image_judges_a_submission_from_inside_a_container_of_its_own(
    judging_service: str,
) -> None:
    answered = httpx2.post(
        f"{judging_service}/submissions",
        json=a_submission_whose_solution_is_correct(A_SUBMISSION_JUDGED_FROM_INSIDE_THE_SERVICE),
        timeout=LONGEST_A_SUBMISSION_IS_WAITED_FOR,
    )

    assert answered.status_code == 200
    assert answered.json()["verdict"] == Verdict.accepted.value


def test_a_submission_judged_from_inside_the_service_leaves_no_container_behind(
    judging_service: str,
) -> None:
    httpx2.post(
        f"{judging_service}/submissions",
        json=a_submission_whose_solution_is_correct(
            A_SUBMISSION_LEAVING_NO_CONTAINER_BEHIND_ON_THE_HOST
        ),
        timeout=LONGEST_A_SUBMISSION_IS_WAITED_FOR,
    )

    assert containers_still_on_the_host() == []


def test_the_service_image_carries_the_docker_client_and_no_part_of_the_sandbox() -> None:
    assert _succeeds_inside(SERVICE_IMAGE, *FINDING_THE_DOCKER_CLIENT)
    assert not _succeeds_inside(SERVICE_IMAGE, *IMPORTING_THE_HARNESS_THE_SANDBOX_RUNS)


def test_the_sandbox_image_carries_no_client_that_could_reach_the_docker_daemon() -> None:
    assert not _succeeds_inside(SANDBOX_IMAGE, *FINDING_THE_DOCKER_CLIENT)


def _succeeds_inside(image: str, *command: str) -> bool:
    ran = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", command[0], image, *command[1:]],
        capture_output=True,
    )
    return ran.returncode == 0


def _the_address_the_service_answers_on() -> str:
    address = f"http://{_the_port_the_service_was_published_on()}"
    give_up_at = time.monotonic() + LONGEST_THE_SERVICE_TAKES_TO_COME_UP
    while time.monotonic() < give_up_at:
        if _the_service_answers_on(address):
            return address
        time.sleep(BETWEEN_ASKING_WHETHER_THE_SERVICE_IS_UP)
    raise TimeoutError(f"the executor service never answered on {address}")


def _the_service_answers_on(address: str) -> bool:
    try:
        return httpx2.get(f"{address}/health").status_code == 200
    except httpx2.HTTPError:
        return False


def _the_port_the_service_was_published_on() -> str:
    published = subprocess.run(
        ["docker", "port", THE_SERVICE_UNDER_TEST, str(THE_PORT_THE_SERVICE_LISTENS_ON)],
        capture_output=True,
        text=True,
        check=True,
    )
    return published.stdout.split()[0]
