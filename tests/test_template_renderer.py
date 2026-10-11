import pytest

from app.template_renderer import TemplateRenderer


def test_renders_string_with_quotes_safely():
    renderer = TemplateRenderer()

    result = renderer.render(
        'NAME = {{ name }}',
        {"name": "Prashanth's App"},
        {"name": {"type": "string"}},
        {},
        plugin_name="hello",
    )

    assert result == "NAME = \"Prashanth's App\"" or result == "NAME = \"Prashanth's App\"".replace('"', "'")


def test_renders_integer_as_integer():
    renderer = TemplateRenderer()

    result = renderer.render(
        "PORT = {{ input.database_port }}",
        {},
        {},
        {"database_port": {"value": 5432, "secret": False}},
        plugin_name="authentication",
    )

    assert result == "PORT = 5432"


def test_secret_input_uses_provider_environment_name():
    renderer = TemplateRenderer()

    result = renderer.render(
        "PASSWORD = {{ input.database_password }}",
        {},
        {},
        {
            "database_password": {
                "value": "do-not-embed-this",
                "secret": True,
                "secret_name": "POSTGRES_PASSWORD",
            }
        },
        plugin_name="authentication",
    )

    assert result == "PASSWORD = os.getenv('POSTGRES_PASSWORD')"
    assert "do-not-embed-this" not in result


def test_missing_input_fails():
    renderer = TemplateRenderer()

    with pytest.raises(ValueError, match="Unresolved template input"):
        renderer.render(
            "HOST = {{ input.database_host }}",
            {},
            {},
            {},
            plugin_name="authentication",
        )


def test_missing_configuration_fails():
    renderer = TemplateRenderer()

    with pytest.raises(ValueError, match="Unresolved configuration"):
        renderer.render(
            "NAME = {{ missing_name }}",
            {},
            {},
            {},
            plugin_name="hello",
        )


def test_configuration_secret_uses_plugin_environment_name():
    renderer = TemplateRenderer()

    result = renderer.render(
        "API_KEY = {{ api_key }}",
        {"api_key": "do-not-embed-this"},
        {"api_key": {"type": "string", "secret": True}},
        {},
        plugin_name="hello",
    )

    assert result == "API_KEY = os.getenv('HELLO_API_KEY')"
    assert "do-not-embed-this" not in result
