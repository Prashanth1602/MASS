import yaml
import pytest

from app.application_generator import ApplicationGenerator
from app.application_service import ApplicationService
from app.code_plugin_generator import CodePluginGenerator
from app.models import ApplicationConfig, BuildRequest
from app.plugin_registry import PluginRegistry
from app.plugin_scaffolder import PluginScaffolder


def test_create_plugin_generates_expected_files(tmp_path):
    scaffolder = PluginScaffolder(tmp_path / "plugins")

    plugin_directory = scaffolder.create("greeting")

    assert (plugin_directory / "plugin.yaml").is_file()
    assert (plugin_directory / "templates" / "router.py").is_file()
    assert (plugin_directory / "templates" / "service.py").is_file()

    manifest = yaml.safe_load(
        (plugin_directory / "plugin.yaml").read_text()
    )

    assert manifest["name"] == "greeting"
    assert manifest["type"] == "code"
    assert manifest["provides"] == ["greeting"]


@pytest.mark.parametrize(
    "name",
    ["", "Greeting", "123plugin", "../outside", "plugin name"],
)
def test_create_plugin_rejects_invalid_names(tmp_path, name):
    scaffolder = PluginScaffolder(tmp_path / "plugins")

    with pytest.raises(ValueError):
        scaffolder.create(name)


def test_create_plugin_does_not_overwrite_existing_directory(tmp_path):
    plugins_directory = tmp_path / "plugins"
    existing_directory = plugins_directory / "greeting"
    existing_directory.mkdir(parents=True)

    marker = existing_directory / "keep.txt"
    marker.write_text("preserve this")

    scaffolder = PluginScaffolder(plugins_directory)

    with pytest.raises(FileExistsError):
        scaffolder.create("greeting")

    assert marker.read_text() == "preserve this"


def test_scaffolded_plugin_passes_validation_and_generates_code(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    scaffolder = PluginScaffolder(tmp_path / "plugins")
    plugin_directory = scaffolder.create("welcome")

    manifest = yaml.safe_load(
        (plugin_directory / "plugin.yaml").read_text(
            encoding="utf-8"
        )
    )
    plugin = {
        **manifest,
        "resolved_configuration": {
            "message": manifest["configuration"]["message"]["default"]
        },
        "resolved_inputs": {},
    }

    generator = CodePluginGenerator()

    generator.validate(plugin)

    output_directory = tmp_path / "generated"
    generated_files = generator.generate(plugin, output_directory)

    router = output_directory / "app" / "welcome" / "router.py"
    service = output_directory / "app" / "welcome" / "service.py"

    assert router.is_file()
    assert service.is_file()
    assert str(router) in generated_files
    assert str(service) in generated_files

    service_content = service.read_text(encoding="utf-8")

    assert "{{ message }}" not in service_content
    assert "Hello from welcome!" in service_content

    compile(
        router.read_text(encoding="utf-8"),
        str(router),
        "exec",
    )
    compile(service_content, str(service), "exec")



def test_scaffolded_plugin_works_through_application_pipeline(tmp_path):
    # 1. Create a fresh plugin in an isolated plugins directory.
    plugins_directory = tmp_path / "plugins"
    scaffolder = PluginScaffolder(plugins_directory)
    plugin_directory = scaffolder.create("welcome")

    # 2. Load the plugin through the real registry.
    registry = PluginRegistry(str(plugins_directory))
    registry.load_plugins()

    assert registry.get("welcome") is not None

    # 3. Build a real request and run application preparation.
    request = BuildRequest(
        application=ApplicationConfig(
            name="welcome-integration-test",
            host_port=8011,
        ),
        plugins={"welcome": {}},
    )

    service = ApplicationService(registry)
    selected_plugins, dependencies = service.prepare(request)

    assert len(selected_plugins) == 1

    plugin = selected_plugins[0]
    assert plugin["name"] == "welcome"
    assert plugin["resolved_configuration"]["message"] == (
        "Hello from welcome!"
    )

    # 4. Generate plugin code and the FastAPI application.
    output_directory = tmp_path / "generated"
    output_directory.mkdir()

    code_generator = CodePluginGenerator()
    code_generator.generate(plugin, output_directory)

    application_generator = ApplicationGenerator()
    application_generator.generate(
        request.application.name,
        output_directory,
        selected_plugins,
    )

    # 5. Verify the complete generated application structure.
    router = output_directory / "app" / "welcome" / "router.py"
    service_file = output_directory / "app" / "welcome" / "service.py"
    main_file = output_directory / "app" / "main.py"
    requirements_file = output_directory / "requirements.txt"

    assert router.is_file()
    assert service_file.is_file()
    assert main_file.is_file()
    assert requirements_file.is_file()

    main_content = main_file.read_text(encoding="utf-8")

    assert "from app.welcome.router import router as welcome_router" in (
        main_content
    )
    assert "app.include_router(welcome_router)" in main_content

    # 6. Check that every generated Python file has valid syntax.
    for python_file in (output_directory / "app").rglob("*.py"):
        compile(
            python_file.read_text(encoding="utf-8"),
            str(python_file),
            "exec",
        )


