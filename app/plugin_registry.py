from pathlib import Path

import yaml
from pydantic import ValidationError

from app.plugin_conformance_validator import PluginConformanceValidator
from app.plugin_schema import PluginDefinition


class PluginRegistry:

    def __init__(self, plugins_directory: str = "plugins"):
        self.plugins_directory = Path(plugins_directory)
        self.plugins = {}
        self.conformance_validator = PluginConformanceValidator()

    def load_plugins(self):
        if not self.plugins_directory.is_dir():
            raise ValueError(
                f"Plugins directory not found: {self.plugins_directory}"
            )

        loaded_plugins = {}

        for plugin_file in sorted(
            self.plugins_directory.glob("*/plugin.yaml")
        ):
            try:
                with plugin_file.open("r", encoding="utf-8") as file:
                    raw_plugin = yaml.safe_load(file)

                if not isinstance(raw_plugin, dict):
                    raise ValueError(
                        "Plugin YAML must contain a mapping"
                    )

                validated = PluginDefinition.model_validate(raw_plugin)
                plugin = validated.model_dump(by_alias=True, exclude_unset=True)

                self.conformance_validator.validate(plugin)

                if plugin["name"] != plugin_file.parent.name:
                    raise ValueError(
                        f"Plugin name '{plugin['name']}' must match "
                        f"its directory name '{plugin_file.parent.name}'"
                    )

                plugin_name = plugin["name"]

                if plugin_name in loaded_plugins:
                    raise ValueError(
                        f"Duplicate plugin name: '{plugin_name}'"
                    )

                loaded_plugins[plugin_name] = plugin

            except (yaml.YAMLError, ValidationError, ValueError) as exc:
                raise ValueError(
                    f"Invalid plugin metadata in '{plugin_file}': {exc}"
                ) from exc

        self.plugins = loaded_plugins

    def get(self, plugin_name: str):
        return self.plugins.get(plugin_name)

    def list_plugins(self):
        return list(self.plugins.values())
