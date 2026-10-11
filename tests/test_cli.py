import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

import app.cli as cli


@pytest.mark.parametrize(
    ("arguments", "handler_name", "handler_args"),
    [
        (["plugins", "list"], "list_plugins", ()),
        (["plugins", "inspect", "postgres"], "inspect_plugin", ("postgres",)),
        (["app", "validate", "movie-api.yaml"], "validate_application", ("movie-api.yaml",)),
        (["app", "build", "movie-api.yaml"], "build_application_from_spec", ("movie-api.yaml",)),
        (["app", "run", "movie-api"], "run_application", ("movie-api",)),
        (["app", "stop", "movie-api"], "stop_application", ("movie-api",)),
    ],
)
def test_main_dispatches_commands(monkeypatch, arguments, handler_name, handler_args):
    handler = Mock(return_value=0)
    monkeypatch.setattr(cli, handler_name, handler)
    monkeypatch.setattr(sys, "argv", ["mass", *arguments])

    result = cli.main()

    assert result == 0
    handler.assert_called_once_with(*handler_args)


def test_main_propagates_command_failure(monkeypatch):
    handler = Mock(return_value=1)
    monkeypatch.setattr(cli, "run_application", handler)
    monkeypatch.setattr(
        sys,
        "argv",
        ["mass", "app", "run", "movie-api"],
    )

    result = cli.main()

    assert result == 1
    handler.assert_called_once_with("movie-api")


def test_validate_application_reports_invalid_specification(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "load_application_spec",
        Mock(side_effect=ValueError("Invalid YAML")),
    )

    result = cli.validate_application("invalid.yaml")

    assert result == 1
    assert "Validation failed: Invalid YAML" in capsys.readouterr().err


def test_build_application_reports_http_error(monkeypatch, capsys):
    specification = SimpleNamespace(
        name="movie-api",
        host_port=8000,
        plugins={"postgres": {}},
    )

    monkeypatch.setattr(
        cli,
        "load_application_spec",
        Mock(return_value=specification),
    )
    monkeypatch.setattr(
        cli,
        "build_application_request",
        Mock(
            side_effect=HTTPException(
                status_code=409,
                detail="Application already exists",
            )
        ),
    )

    result = cli.build_application_from_spec("movie-api.yaml")

    assert result == 1
    assert "Application already exists" in capsys.readouterr().err



def test_build_application_reports_invalid_specification(monkeypatch, capsys,):
    monkeypatch.setattr(
        cli,
        "load_application_spec",
        Mock(
            side_effect=ValueError(
                "Environment variable is not set"
            )
        ),
    )

    result = cli.build_application_from_spec("movie-api.yaml")

    captured = capsys.readouterr()

    assert result == 1
    assert "Build failed:" in captured.err
    assert "Environment variable is not set" in captured.err



def test_cli_help_lists_commands(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["mass", "app", "--help"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0

    output = capsys.readouterr().out
    assert "validate" in output
    assert "build" in output
    assert "run" in output
    assert "stop" in output
