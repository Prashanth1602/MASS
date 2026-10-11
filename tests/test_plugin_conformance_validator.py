
import pytest

from app.plugin_conformance_validator import (
    PluginConformanceValidator,
)
from app.plugin_registry import PluginRegistry


@pytest.fixture
def validator():
    return PluginConformanceValidator()


def test_existing_plugins_pass_conformance():
    registry = PluginRegistry()
    registry.load_plugins()

    validator = PluginConformanceValidator()

    for plugin in registry.list_plugins():
        validator.validate(plugin)


def test_rejects_duplicate_capability(validator):
    plugin = {
        "name": "sample",
        "provides": ["database", "database"],
    }

    with pytest.raises(ValueError, match="duplicate 'provides'"):
        validator.validate(plugin)


def test_rejects_default_with_wrong_type(validator):
    plugin = {
        "name": "sample",
        "configuration": {
            "port": {
                "type": "integer",
                "default": "not-a-port",
            }
        },
    }

    with pytest.raises(ValueError, match="wrong type"):
        validator.validate(plugin)


def test_rejects_unknown_environment_placeholder(validator):
    plugin = {
        "name": "sample",
        "configuration": {
            "database": {"type": "string"},
        },
        "environment": {
            "DATABASE_URL": "{{ missing_key }}",
        },
    }

    with pytest.raises(ValueError, match="unknown configuration key"):
        validator.validate(plugin)


def test_rejects_malformed_input_reference(validator):
    plugin = {
        "name": "sample",
        "inputs": {
            "database_host": {"from": "database"},
        },
    }

    with pytest.raises(ValueError, match="capability.output"):
        validator.validate(plugin)


def test_rejects_duplicate_runtime_dependency(validator):
    plugin = {
        "name": "sample",
        "runtime_dependencies": ["redis", "redis"],
    }

    with pytest.raises(ValueError, match="duplicate runtime dependency"):
        validator.validate(plugin)
