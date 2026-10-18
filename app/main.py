import shutil
import tempfile

from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.application_generator import ApplicationGenerator
from app.build_lock import application_build_lock
from app.code_plugin_generator import CodePluginGenerator
from app.compose_generator import ComposeGenerator
from app.config_resolver import ConfigResolver
from app.dependency_resolver import DependencyResolver
from app.input_resolver import InputResolver
from app.models import BuildRequest
from app.output_resolver import OutputResolver
from app.plugin_contract_validator import PluginContractValidator
from app.plugin_registry import PluginRegistry
from app.runtime_dependency_resolver import RuntimeDependencyResolver
from app.application_service import ApplicationService, PluginNotFoundError

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mass")

app = FastAPI(
    title="MASS - Modular Application Service Stack",
    version="0.1.0"
)

registry = PluginRegistry()
registry.load_plugins()

application_service = ApplicationService(registry)

compose_generator = ComposeGenerator()

config_resolver = ConfigResolver()

dependency_resolver = DependencyResolver()

code_generator = CodePluginGenerator(plugins_directory=str(registry.plugins_directory))

output_resolver = OutputResolver()

input_resolver = InputResolver()

application_generator = ApplicationGenerator()

runtime_dependency_resolver = RuntimeDependencyResolver()

plugin_contract_validator = PluginContractValidator()

@app.get("/")
def root():
    return {
        "message": "MASS - Modular Application Service Stack is running"
    }

@app.post("/build")
def build_application(request: BuildRequest):
    try:
        selected_plugins, dependencies = application_service.prepare(
            request
        )

    except PluginNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    generated_root = Path("generated")
    generated_root.mkdir(parents=True, exist_ok=True)

    application_name = request.application.name
    output_directory = generated_root / application_name

    with application_build_lock(generated_root, application_name):
        if output_directory.exists():
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Application '{application_name}' already exists. "
                    "Choose a different name."
                ),
            )

        staging_directory = Path(
            tempfile.mkdtemp(
                prefix=f".{application_name}.staging-",
                dir=generated_root,
            )
        )

        try:
            for plugin in selected_plugins:
                if plugin["type"] == "code":
                    code_generator.generate(
                        plugin,
                        staging_directory,
                    )

            env_content = compose_generator.generate_env_file(selected_plugins)
            env_file = staging_directory / ".env"
            env_file.write_text(env_content)
            env_file.chmod(0o600)

            (staging_directory / ".gitignore").write_text(
                ".env\n__pycache__/\n*.pyc\n"
            )

            application_generator.generate(
                application_name,
                staging_directory,
                selected_plugins,
            )

            runtime_dependencies = runtime_dependency_resolver.resolve(dependencies, selected_plugins)

            compose_content = compose_generator.generate(application_name, selected_plugins, runtime_dependencies, host_port=request.application.host_port)

            (staging_directory / "host_port").write_text(
                f"{request.application.host_port}\n",
                encoding="utf-8",
            )

            (staging_directory / "docker-compose.yml"
            ).write_text(compose_content)

            staging_directory.rename(output_directory)

        except HTTPException:
            shutil.rmtree(staging_directory, ignore_errors=True)
            raise

        except Exception:
            logger.exception(
                    "Application generation failed for '%s'",
                    application_name,
            )

            shutil.rmtree(staging_directory, ignore_errors=True)
            raise HTTPException(
                    status_code=500,
                    detail=(
                        "Application generation failed. "
                        "No new application was published."
                    ),
                ) from None

        return {
            "message": "Application generated successfully",
            "application": application_name,
            "plugins": list(request.plugins.keys()),
            "dependencies": dependencies,
            "compose_file": str(
                output_directory / "docker-compose.yml"
            ),
        }

@app.get("/plugins")
def list_plugins():
    return registry.list_plugins()


@app.get("/plugins/{plugin_name}")
def get_plugin(plugin_name: str):

    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin '{plugin_name}' not found"
        )

    return plugin