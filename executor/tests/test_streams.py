import subprocess
import sys
import threading

from executor.streams import send_and_collect

WRITES_BEFORE_IT_READS = (
    "import sys; sys.stdout.write('o' * 200000); sys.stdout.flush();"
    " sys.stdin.read(); sys.stdout.write('done')"
)


def test_a_process_writing_before_it_has_read_its_input_does_not_deadlock() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", WRITES_BEFORE_IT_READS],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    )
    collected: list[str] = []

    def collect() -> None:
        collected.append(send_and_collect(process, "i" * 200_000))

    collecting = threading.Thread(target=collect)
    collecting.start()
    collecting.join(timeout=30)
    process.kill()

    assert collected == ["o" * 200_000 + "done"]
