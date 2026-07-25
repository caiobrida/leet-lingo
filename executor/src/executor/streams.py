import subprocess
import threading
from typing import IO, cast


def send_and_collect(process: "subprocess.Popen[str]", payload: str) -> str:
    def write_until_the_process_stops_reading(stream: IO[str]) -> None:
        try:
            with stream:
                stream.write(payload)
        except OSError:
            pass

    writing = threading.Thread(
        target=write_until_the_process_stops_reading,
        args=(process.stdin,),
    )
    writing.start()
    with cast(IO[str], process.stdout) as stdout:
        collected = stdout.read()
    writing.join()
    return collected
