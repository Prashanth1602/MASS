
from app.compose_generator import ComposeGenerator


def test_secret_environment_uses_canonical_variable_name():
    generator = ComposeGenerator()

    result = generator.generate(
        "test_app",
        [
            {
                "name": "postgres",
                "type": "container",
                "image": {
                    "repository": "postgres",
                    "tag": "18",
                },
                "configuration": {
                    "password": {
                        "type": "string",
                        "secret": True,
                    }
                },
                "resolved_configuration": {
                    "password": "dummy-secret",
                },
                "environment": {
                    "POSTGRES_PASSWORD": "{{ password }}",
                },
            }
        ],
        {},
    )

    assert "${POSTGRES_PASSWORD}" in result
    assert "${password}" not in result


def test_app_service_uses_env_file():
    generator = ComposeGenerator()

    service = generator.build_application_service(["postgres"])

    assert service["env_file"] == [".env"]
    assert service["depends_on"] == ["postgres"]


def test_application_service_uses_configured_host_port():
    generator = ComposeGenerator()

    service = generator.build_application_service(
        dependencies=[],
        host_port=8001,
    )

    assert service["ports"] == ["8001:8000"]

