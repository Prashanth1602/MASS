
import pytest

from app.dependency_resolver import DependencyResolver


def test_resolves_required_capabilities():
    plugins = [
        {
            "name": "postgres",
            "provides": ["database"],
        },
        {
            "name": "redis",
            "provides": ["key_value_store"],
        },
        {
            "name": "authentication",
            "type": "code",
            "requires": ["database", "key_value_store"],
        },
    ]

    result = DependencyResolver().resolve(plugins)

    assert result["authentication"] == {
        "database": "postgres",
        "key_value_store": "redis",
    }


def test_fails_when_provider_is_missing():
    plugins = [
        {
            "name": "authentication",
            "requires": ["database"],
        }
    ]

    with pytest.raises(ValueError, match="no selected plugin provides"):
        DependencyResolver().resolve(plugins)


def test_fails_when_provider_is_ambiguous():
    plugins = [
        {"name": "postgres", "provides": ["database"]},
        {"name": "another_db", "provides": ["database"]},
        {"name": "authentication", "requires": ["database"]},
    ]

    with pytest.raises(ValueError, match="multiple selected plugins"):
        DependencyResolver().resolve(plugins)


def test_rejects_self_dependency():
    plugins = [
        {
            "name": "plugin_a",
            "provides": ["service_a"],
            "requires": ["service_a"],
        }
    ]

    with pytest.raises(ValueError, match="cannot satisfy its own"):
        DependencyResolver().resolve(plugins)


def test_rejects_two_plugin_dependency_cycle():
    plugins = [
        {
            "name": "plugin_a",
            "provides": ["service_a"],
            "requires": ["service_b"],
        },
        {
            "name": "plugin_b",
            "provides": ["service_b"],
            "requires": ["service_a"],
        },
    ]

    with pytest.raises(ValueError, match="Dependency cycle detected"):
        DependencyResolver().resolve(plugins)


def test_rejects_longer_dependency_cycle():
    plugins = [
        {
            "name": "plugin_a",
            "provides": ["service_a"],
            "requires": ["service_b"],
        },
        {
            "name": "plugin_b",
            "provides": ["service_b"],
            "requires": ["service_c"],
        },
        {
            "name": "plugin_c",
            "provides": ["service_c"],
            "requires": ["service_a"],
        },
    ]

    with pytest.raises(ValueError, match="Dependency cycle detected"):
        DependencyResolver().resolve(plugins)

