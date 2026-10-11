import subprocess
from unittest.mock import Mock

from app.runtime_manager import run_application, stop_application


def create_application(tmp_path):
    app_dir = tmp_path / "movie-api"
    app_dir.mkdir()
    (app_dir / "docker-compose.yml").write_text("services: {}\n")
    return app_dir


def test_run_application_success(tmp_path, monkeypatch, capsys):
    create_application(tmp_path)
    mock_run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr("app.runtime_manager.subprocess.run", mock_run)

    result = run_application("movie-api", generated_root=tmp_path)

    assert result == 0
    mock_run.assert_called_once_with(
        ["docker", "compose", "up", "-d", "--build"],
        cwd=tmp_path / "movie-api",
        check=False,
    )
    assert "started successfully" in capsys.readouterr().out


def test_stop_application_success(tmp_path, monkeypatch):
    create_application(tmp_path)
    mock_run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr("app.runtime_manager.subprocess.run", mock_run)

    result = stop_application("movie-api", generated_root=tmp_path)

    assert result == 0
    mock_run.assert_called_once_with(
        ["docker", "compose", "down"],
        cwd=tmp_path / "movie-api",
        check=False,
    )


def test_missing_application_does_not_run_docker(tmp_path, monkeypatch, capsys):
    mock_run = Mock()
    monkeypatch.setattr("app.runtime_manager.subprocess.run", mock_run)

    result = run_application("missing-app", generated_root=tmp_path)

    assert result == 1
    mock_run.assert_not_called()
    assert "not found" in capsys.readouterr().err


def test_invalid_application_name_is_rejected(tmp_path, monkeypatch):
    mock_run = Mock()
    monkeypatch.setattr("app.runtime_manager.subprocess.run", mock_run)

    result = run_application("../other-app", generated_root=tmp_path)

    assert result == 1
    mock_run.assert_not_called()


def test_docker_not_installed_returns_error(tmp_path, monkeypatch, capsys):
    create_application(tmp_path)

    def raise_missing_docker(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(
        "app.runtime_manager.subprocess.run",
        raise_missing_docker,
    )

    result = run_application("movie-api", generated_root=tmp_path)

    assert result == 1
    assert "Docker was not found" in capsys.readouterr().err


def test_compose_failure_returns_error(tmp_path, monkeypatch, capsys):
    create_application(tmp_path)
    mock_run = Mock(return_value=Mock(returncode=1))
    monkeypatch.setattr("app.runtime_manager.subprocess.run", mock_run)

    result = run_application("movie-api", generated_root=tmp_path)

    assert result == 1
    assert "exit code 1" in capsys.readouterr().err


def test_failed_startup_attempts_cleanup(tmp_path, monkeypatch, capsys):
    create_application(tmp_path)

    mock_run = Mock(
        side_effect=[
            subprocess.CompletedProcess(
                args=["docker", "compose", "up"],
                returncode=1,
            ),
            subprocess.CompletedProcess(
                args=["docker", "compose", "down"],
                returncode=0,
            ),
        ]
    )
    monkeypatch.setattr(
        "app.runtime_manager.subprocess.run",
        mock_run,
    )

    result = run_application(
        "movie-api",
        generated_root=tmp_path,
    )

    assert result == 1
    assert mock_run.call_count == 2

    assert mock_run.call_args_list[0].args[0] == [
        "docker", "compose", "up", "-d", "--build"
    ]
    assert mock_run.call_args_list[1].args[0] == [
        "docker", "compose", "down"
    ]

    captured = capsys.readouterr()
    assert "exit code 1" in captured.err
    assert "Attempting to clean up" in captured.err

