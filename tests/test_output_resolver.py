
from app.output_resolver import OutputResolver


def test_container_host_uses_service_name():
    plugin = {
        "name": "postgres",
        "type": "container",
        "outputs": {
            "host": {"value": "localhost"},
            "port": {"value": "{{ port }}"},
        },
        "resolved_configuration": {"port": 5432},
    }

    result = OutputResolver().resolve(plugin)

    assert result["host"]["value"] == "postgres"
    assert result["port"]["value"] == 5432


def test_secret_output_has_canonical_env_name():
    plugin = {
        "name": "postgres",
        "type": "container",
        "outputs": {
            "password": {
                "value": "{{ password }}",
                "secret": True,
            }
        },
        "resolved_configuration": {
            "password": "test-secret",
        },
    }

    result = OutputResolver().resolve(plugin)

    assert result["password"]["secret"] is True
    assert result["password"]["secret_name"] == "POSTGRES_PASSWORD"
