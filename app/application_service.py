from app.code_plugin_generator import CodePluginGenerator
from app.config_resolver import ConfigResolver
from app.dependency_resolver import DependencyResolver
from app.input_resolver import InputResolver
from app.output_resolver import OutputResolver
from app.plugin_contract_validator import PluginContractValidator


class PluginNotFoundError(ValueError):
    pass


class ApplicationService:
    def __init__(self, registry):
        self.registry = registry
        self.config_resolver = ConfigResolver()
        self.dependency_resolver = DependencyResolver()
        self.input_resolver = InputResolver()
        self.output_resolver = OutputResolver()
        self.contract_validator = PluginContractValidator()
        self.code_plugin_generator = CodePluginGenerator(plugins_directory=str(registry.plugins_directory))

    def prepare(self, request):
        selected_plugins = []

        for plugin_name, user_config in request.plugins.items():
            plugin = self.registry.get(plugin_name)

            if plugin is None:
                raise PluginNotFoundError(
                    f"Plugin '{plugin_name}' not found"
                )

            resolved_config = self.config_resolver.resolve(
                plugin, user_config
            )

            plugin_copy = plugin.copy()
            plugin_copy["resolved_configuration"] = resolved_config
            selected_plugins.append(plugin_copy)

        dependencies = self.dependency_resolver.resolve(
            selected_plugins
        )

        self.contract_validator.validate(
            selected_plugins, dependencies
        )

        for plugin in selected_plugins:
            plugin["resolved_outputs"] = self.output_resolver.resolve(
                plugin
            )

        resolved_plugin_map = {
            plugin["name"]: plugin
            for plugin in selected_plugins
        }

        for plugin in selected_plugins:
            plugin["resolved_inputs"] = self.input_resolver.resolve(
                plugin,
                dependencies,
                resolved_plugin_map,
            )

        for plugin in selected_plugins:
            if plugin.get("type") == "code":
                self.code_plugin_generator.validate(plugin)

        return selected_plugins, dependencies
