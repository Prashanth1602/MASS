from pathlib import Path
import re


PLUGIN_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")


class PluginScaffolder:
    def __init__(self, plugins_directory: Path | None = None):
        self.plugins_directory = (
            Path(plugins_directory)
            if plugins_directory is not None
            else Path("plugins")
        )

    def create(self, name: str) -> Path:
        if not PLUGIN_NAME_PATTERN.fullmatch(name):
            raise ValueError(
                "Plugin name must start with a lowercase letter and "
                "contain only lowercase letters, numbers, underscores, "
                "or hyphens."
            )

        plugin_directory = self.plugins_directory / name

        if plugin_directory.exists():
            raise FileExistsError(
                f"Plugin directory already exists: {plugin_directory}"
            )

        templates_directory = plugin_directory / "templates"

        try:
            templates_directory.mkdir(parents=True)

            manifest = f'''apiVersion: mass/v1
name: {name}
version: "1.0"

type: code

provides:
  - {name.replace("-", "_")}

configuration:
  message:
    type: string
    required: false
    default: Hello from {name}!
'''

            router = '''from fastapi import APIRouter

from .service import get_message

router = APIRouter(prefix="/''' + name + '''", tags=["''' + name + '''"])


@router.get("/")
def get_greeting():
    return {"message": get_message()}
'''

            service = '''def get_message():
    return {{ message }}
'''

            (plugin_directory / "plugin.yaml").write_text(
                manifest, encoding="utf-8"
            )
            (templates_directory / "router.py").write_text(
                router, encoding="utf-8"
            )
            (templates_directory / "service.py").write_text(
                service, encoding="utf-8"
            )

        except Exception:
            import shutil
            shutil.rmtree(plugin_directory, ignore_errors=True)
            raise

        return plugin_directory
