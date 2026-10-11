
from contextlib import contextmanager
import fcntl
from pathlib import Path

from fastapi import HTTPException


@contextmanager
def application_build_lock(
    generated_root: Path,
    application_name: str,
):
    lock_directory = generated_root / ".locks"
    lock_directory.mkdir(parents=True, exist_ok=True)

    lock_path = lock_directory / f"{application_name}.lock"

    with lock_path.open("a+") as lock_file:
        try:
            fcntl.flock(
                lock_file.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError as exc:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Build for application '{application_name}' "
                    "is already in progress."
                ),
            ) from exc

        try:
            yield
        finally:
            fcntl.flock(
                lock_file.fileno(),
                fcntl.LOCK_UN,
            )
