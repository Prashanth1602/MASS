from pathlib import Path
import yaml


class PluginRegistry:

    def __init__(self, plugins_directory: str = "plugins"):
        self.plugins_directory = Path(plugins_directory)
        self.plugins = {}

    def load_plugins(self):
        for plugin_file in self.plugins_directory.glob("*/plugin.yaml"):

            with open(plugin_file, "r") as file:
                plugin = yaml.safe_load(file)

            plugin_name = plugin["name"]

            self.plugins[plugin_name] = plugin

    def get(self, plugin_name: str):
        return self.plugins.get(plugin_name)

    def list_plugins(self):
        return list(self.plugins.values())
    