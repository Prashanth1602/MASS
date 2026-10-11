import re
import subprocess
import sys
from pathlib import Path


APPLICATION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _run_compose_command(
    application_name: str,
    command: list[str],
    generated_root: Path = Path("generated"),
    cleanup_on_failure: bool = False
) -> int:
    if not APPLICATION_NAME_PATTERN.fullmatch(application_name):
        print(
            f"Invalid application name: '{application_name}'",
            file=sys.stderr,
        )
        return 1

    application_directory = generated_root / application_name
    compose_file = application_directory / "docker-compose.yml"

    if not application_directory.is_dir() or not compose_file.is_file():
        print(
            f"Generated application '{application_name}' not found. "
            f"Expected: {compose_file}",
            file=sys.stderr,
        )
        return 1

    try:
        result = subprocess.run(
            ["docker", "compose", *command],
            cwd=application_directory,
            check=False,
        )
    except FileNotFoundError:
        print(
            "Docker was not found. Install Docker Desktop "
            "and ensure the Docker CLI is available.",
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print(f"Could not execute Docker Compose: {exc}", file=sys.stderr)
        return 1

    
    if result.returncode != 0:
        print(
            f"Docker Compose failed for '{application_name}' "
            f"with exit code {result.returncode}.",
            file=sys.stderr,
        )

        if cleanup_on_failure:
            print(
                f"Attempting to clean up '{application_name}'...",
                file=sys.stderr,
            )

            try:
                cleanup_result = subprocess.run(
                    ["docker", "compose", "down"],
                    cwd=application_directory,
                    check=False,
                )

                if cleanup_result.returncode != 0:
                    print(
                        f"Cleanup also failed for '{application_name}' "
                        f"with exit code {cleanup_result.returncode}.",
                        file=sys.stderr,
                    )
            except (OSError, FileNotFoundError) as exc:
                print(
                    f"Could not clean up '{application_name}': {exc}",
                    file=sys.stderr,
                )

        return 1

    return 0



def run_application(application_name: str, generated_root: Path = Path("generated")) -> int:
    print(f"Starting application '{application_name}'...")
    result = _run_compose_command(application_name, ["up", "-d", "--build"], generated_root, cleanup_on_failure=True)
    if result == 0:
        print(f"Application '{application_name}' started successfully.")
    return result


def stop_application(application_name: str, generated_root: Path = Path("generated")) -> int:
    print(f"Stopping application '{application_name}'...")
    result = _run_compose_command(
        application_name,
        ["down"],
        generated_root,
    )

    if result == 0:
        print(f"Application '{application_name}' stopped successfully.")

    return result
