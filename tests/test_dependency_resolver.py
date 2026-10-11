
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
