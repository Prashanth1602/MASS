from pathlib import Path

from fastapi import FastAPI

from app.application_generator import ApplicationGenerator
from app.code_plugin_generator import CodePluginGenerator
from app.compose_generator import ComposeGenerator
from app.config_resolver import ConfigResolver
from app.dependency_resolver import DependencyResolver
from app.input_resolver import InputResolver
from app.models import BuildRequest
from app.output_resolver import OutputResolver
from app.plugin_registry import PluginRegistry
from app.runtime_dependency_resolver import RuntimeDependencyResolver

app = FastAPI(
    title="MASS - Modular Application Service Stack",
    version="0.1.0"
)

registry = PluginRegistry()
registry.load_plugins()

compose_generator = ComposeGenerator()

config_resolver = ConfigResolver()

dependency_resolver = DependencyResolver()

code_generator = CodePluginGenerator()

output_resolver = OutputResolver()

input_resolver = InputResolver()

application_generator = ApplicationGenerator()

runtime_dependency_resolver = RuntimeDependencyResolver()

@app.get("/")
def root():
    return {
        "message": "MASS - Modular Application Service Stack is running"
    }


@app.post("/build")
def build_application(request: BuildRequest):

    selected_plugins = []

    for plugin_name, user_config in request.plugins.items():

        plugin = registry.get(plugin_name)

        if plugin is None:
            return {
                "error": f"Plugin '{plugin_name}' not found"
            }

        try:
            resolved_config = config_resolver.resolve(plugin, user_config)
            secret_config = config_resolver.get_secret_fields(plugin, resolved_config)
        except ValueError as e:
            return {
                "error": str(e)
            }

        plugin_copy = plugin.copy()
        plugin_copy["resolved_configuration"] = resolved_config
        selected_plugins.append(plugin_copy)

    

    dependencies = dependency_resolver.resolve(selected_plugins)

    for plugin in selected_plugins:
        resolved_outputs = output_resolver.resolve(plugin)
        plugin["resolved_outputs"] = resolved_outputs

    resolved_plugin_map = {
        plugin["name"]: plugin
        for plugin in selected_plugins
    }

    for plugin in selected_plugins:
        resolved_inputs = input_resolver.resolve(
        plugin,
        dependencies,
        resolved_plugin_map
    )

        plugin["resolved_inputs"] = resolved_inputs

    output_directory = Path("generated") / request.application.name
    output_directory.mkdir(parents=True, exist_ok=True)

    generated_code_files = []

    for plugin in selected_plugins:
        if plugin["type"] != "code":
            continue

        files = code_generator.generate(plugin, output_directory)
        generated_code_files.extend(files)

    env_content = compose_generator.generate_env_file(selected_plugins)
    env_file = output_directory / ".env"
    env_file.write_text(env_content)
    env_file.chmod(0o600)

    gitignore_file = output_directory / ".gitignore"
    gitignore_file.write_text(".env\n__pycache__/\n*.pyc\n")

    application_generator.generate(
        request.application.name,
        output_directory,
        selected_plugins
    )

    runtime_dependencies = runtime_dependency_resolver.resolve(
        dependencies,
        selected_plugins
    )

    compose_content = compose_generator.generate(
        request.application.name,
        selected_plugins,
        runtime_dependencies
    )

    compose_file = output_directory / "docker-compose.yml"
    compose_file.write_text(compose_content)


    return {
        "message": "Application generated successfully",
        "application": request.application.name,
        "plugins": list(request.plugins.keys()),
        "dependencies": dependencies,
        "compose_file": str(compose_file) 
    }

@app.get("/plugins")
def list_plugins():
    return registry.list_plugins()


@app.get("/plugins/{plugin_name}")
def get_plugin(plugin_name: str):

    plugin = registry.get(plugin_name)

    if plugin is None:
        return {
            "error": "Plugin not found"
        }

    return plugin