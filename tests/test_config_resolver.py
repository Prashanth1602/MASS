
import pytest

from app.config_resolver import ConfigResolver


@pytest.fixture
def resolver():
    return ConfigResolver()


@pytest.fixture
def plugin():
    return {
        "name": "example",
        "configuration": {
            "name": {
                "type": "string",
                "required": True,
            },
            "port": {
                "type": "integer",
                "required": False,
                "default": 8080,
            },
            "enabled": {
                "type": "boolean",
                "required": False,
                "default": True,
            },
            "ratio": {
                "type": "number",
                "required": False,
                "default": 1.5,
            },
        },
    }


def test_resolves_valid_values_and_defaults(resolver, plugin):
    result = resolver.resolve(
        plugin,
        {"name": "MASS"},
    )

    assert result == {
        "name": "MASS",
        "port": 8080,
        "enabled": True,
        "ratio": 1.5,
    }


def test_rejects_missing_required_value(resolver, plugin):
    with pytest.raises(ValueError, match="Missing required"):
        resolver.resolve(plugin, {})


def test_rejects_unknown_key(resolver, plugin):
    with pytest.raises(ValueError, match="Unknown configuration key"):
        resolver.resolve(
            plugin,
            {"name": "MASS", "porrt": 8080},
        )


@pytest.mark.parametrize(
    ("key", "value", "expected"),
    [
        ("name", 123, "string"),
        ("port", "abc", "integer"),
        ("port", True, "integer"),
        ("enabled", 1, "boolean"),
        ("ratio", False, "number"),
    ],
)
def test_rejects_wrong_types(
    resolver,
    plugin,
    key,
    value,
    expected,
):
    with pytest.raises(ValueError, match=f"expected {expected}"):
        resolver.resolve(
            plugin,
            {"name": "MASS", key: value},
        )


def test_accepts_integer_for_number(resolver, plugin):
    result = resolver.resolve(
        plugin,
        {"name": "MASS", "ratio": 2},
    )

    assert result["ratio"] == 2


def test_rejects_invalid_default(resolver):
    invalid_plugin = {
        "name": "example",
        "configuration": {
            "port": {
                "type": "integer",
                "default": "not-a-port",
            },
        },
    }

    with pytest.raises(ValueError, match="expected integer"):
        resolver.resolve(invalid_plugin, {})


import pytest
from pydantic import ValidationError

from app.models import ApplicationConfig


def test_application_config_defaults_to_port_8000():
    config = ApplicationConfig(name="movie-api")

    assert config.host_port == 8000


@pytest.mark.parametrize("port", [0, 65536, -1])
def test_application_config_rejects_invalid_host_port(port):
    with pytest.raises(ValidationError):
        ApplicationConfig(
            name="movie-api",
            host_port=port,
        )

