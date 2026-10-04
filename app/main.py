from pathlib import Path

from fastapi import FastAPI

from app.compose_generator import ComposeGenerator
from app.models import BuildRequest
from app.plugin_registry import PluginRegistry

app = FastAPI(
    title="MASS - Modular Application Service Stack",
    version="0.1.0"
)

registry = PluginRegistry()
registry.load_plugins()

compose_generator = ComposeGenerator()

@app.get("/")
def root():
    return {
        "message": "MASS - Modular Application Service Stack is running"
    }


@app.post("/build")
def build_application(request: BuildRequest):

    selected_plugins = []

    for plugin_name in request.plugins:

        plugin = registry.get(plugin_name)

        if plugin is None:
            return {
                "error": f"Plugin '{plugin_name}' not found"
            }

        selected_plugins.append(plugin)

    compose_yaml = compose_generator.generate(
        application_name=request.application.name,
        plugins=selected_plugins
    )

    output_directory = Path("generated") / request.application.name
    output_directory.mkdir(parents=True, exist_ok=True)

    compose_file = output_directory / "docker-compose.yml"

    compose_file.write_text(compose_yaml)

    return {
        "message": "Application generated successfully",
        "application": request.application.name,
        "plugins": request.plugins,
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