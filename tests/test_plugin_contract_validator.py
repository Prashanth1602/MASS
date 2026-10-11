import pytest

from app.plugin_contract_validator import PluginContractValidator

def provider_plugin(outputs):
    return {
        "name": "postgres",
        "type": "container",
        "provides": ["database"],
        "outputs": outputs,
    }


def consumer_plugin(inputs, requires=None):
    return {
        "name": "authentication",
        "type": "code",
        "requires": ["database"] if requires is None else requires,
        "inputs": inputs,
    }


def test_accepts_input_when_provider_declares_output():
    plugins = [
        provider_plugin({
            "host": {"value": "localhost"},
            "password": {
                "value": "{{ password }}",
                "secret": True,
            },
        }),
        consumer_plugin({
            "database_host": {"from": "database.host"},
            "database_password": {"from": "database.password"},
        }),
    ]

    dependencies = {
        "postgres": {},
        "authentication": {"database": "postgres"},
    }

    PluginContractValidator().validate(plugins, dependencies)


def test_rejects_input_when_provider_output_is_missing():
    plugins = [
        provider_plugin({
            "host": {"value": "localhost"},
        }),
        consumer_plugin({
            "database_password": {"from": "database.password"},
        }),
    ]

    dependencies = {
        "postgres": {},
        "authentication": {"database": "postgres"},
    }

    with pytest.raises(ValueError, match="does not declare output 'password'"):
        PluginContractValidator().validate(plugins, dependencies)


def test_rejects_input_from_undeclared_capability():
    plugins = [
        provider_plugin({
            "host": {"value": "localhost"},
        }),
        consumer_plugin(
            {"database_host": {"from": "database.host"}},
            requires=[],
        ),
    ]

    dependencies = {
        "postgres": {},
        "authentication": {},
    }

    with pytest.raises(ValueError, match="not declared in 'requires'"):
        PluginContractValidator().validate(plugins, dependencies)


def test_rejects_malformed_input_reference():
    plugins = [
        provider_plugin({
            "host": {"value": "localhost"},
        }),
        consumer_plugin({
            "database_host": {"from": "database"},
        }),
    ]

    dependencies = {
        "postgres": {},
        "authentication": {"database": "postgres"},
    }

    with pytest.raises(ValueError, match="capability.output"):
        PluginContractValidator().validate(plugins, dependencies)


def test_rejects_missing_resolved_provider():
    plugins = [
        provider_plugin({
            "host": {"value": "localhost"},
        }),
        consumer_plugin({
            "database_host": {"from": "database.host"},
        }),
    ]

    dependencies = {
        "postgres": {},
        "authentication": {},
    }

    with pytest.raises(ValueError, match="no resolved provider"):
        PluginContractValidator().validate(plugins, dependencies)
