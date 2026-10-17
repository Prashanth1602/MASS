import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


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


def status_application(application_name: str, generated_root: Path = Path("generated")) -> int:
    print(f"Checking status of application '{application_name}'...")

    return _run_compose_command(
        application_name,
        ["ps"],
        generated_root,
    )


def logs_application(application_name: str, follow: bool = False, generated_root: Path = Path("generated")) -> int:
    print(f"Showing logs for application '{application_name}'...")

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

    command = ["docker", "compose", "logs"]
    if follow:
        command.append("--follow")

    try:
        result = subprocess.run(
            command,
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
    except KeyboardInterrupt:
        print("\nStopped following logs.")
        return 0

    if result.returncode != 0:
        print(
            f"Could not retrieve logs for '{application_name}' "
            f"(exit code {result.returncode}).",
            file=sys.stderr,
        )
        return 1

    return 0


def health_application(application_name: str, port: int | None = None, generated_root: Path = Path("generated")) -> int:
    if not APPLICATION_NAME_PATTERN.fullmatch(application_name):
        print(f"Invalid application name: '{application_name}'", file=sys.stderr)
        return 1

    application_directory = generated_root / application_name
    compose_file = application_directory / "docker-compose.yml"

    if not application_directory.is_dir() or not compose_file.is_file():
        print(f"Application '{application_name}' not found.", file=sys.stderr)
        return 1

    port_file = application_directory / "host_port"

    if port is None:
        try:
            port = int(port_file.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            port = 8000

    if not 1 <= port <= 65535:
        print("Invalid port: must be between 1 and 65535.", file=sys.stderr)
        return 1

    print(f"Checking health of '{application_name}'...")

    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--status", "running", "--services"],
            cwd=application_directory,
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError) as exc:
        print(f"Could not check container status: {exc}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print("Could not retrieve Docker Compose status.", file=sys.stderr)
        return 1

    if "app" not in result.stdout.splitlines():
        print("NOT RUNNING: application container is not running.")
        return 1

    try:
        with urlopen(f"http://127.0.0.1:{port}/", timeout=3) as response:
            if 200 <= response.status < 300:
                print("HEALTHY: application is responding successfully.")
                return 0

            print(f"UNHEALTHY: HTTP status {response.status}.")
            return 1

    except HTTPError as exc:
        print(f"UNHEALTHY: application returned HTTP {exc.code}.")
        return 1
    except (URLError, TimeoutError, OSError) as exc:
        print(f"UNHEALTHY: application is not reachable ({exc}).")
        return 1



