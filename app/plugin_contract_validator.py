
class PluginContractValidator:

    def validate(self, plugins: list[dict], dependencies: dict) -> None:
        plugin_map = {
            plugin["name"]: plugin
            for plugin in plugins
        }

        for plugin in plugins:
            plugin_name = plugin["name"]
            declared_requirements = set(
                plugin.get("requires", [])
            )
            resolved_dependencies = dependencies.get(plugin_name, {})

            for input_name, definition in plugin.get("inputs", {}).items():
                source = definition.get("from")

                if not isinstance(source, str) or source.count(".") != 1:
                    raise ValueError(
                        f"Plugin '{plugin_name}' input "
                        f"'{input_name}' must reference an output "
                        "using 'capability.output' format"
                    )

                capability, output_name = source.split(".", 1)

                if capability not in declared_requirements:
                    raise ValueError(
                        f"Plugin '{plugin_name}' input "
                        f"'{input_name}' references capability "
                        f"'{capability}', which is not declared "
                        "in 'requires'"
                    )

                provider_name = resolved_dependencies.get(capability)

                if provider_name is None:
                    raise ValueError(
                        f"Plugin '{plugin_name}' input "
                        f"'{input_name}' has no resolved provider "
                        f"for capability '{capability}'"
                    )

                provider = plugin_map.get(provider_name)

                if provider is None:
                    raise ValueError(
                        f"Resolved provider '{provider_name}' "
                        f"for plugin '{plugin_name}' was not selected"
                    )

                provider_outputs = provider.get("outputs", {})

                if output_name not in provider_outputs:
                    raise ValueError(
                        f"Plugin '{plugin_name}' input "
                        f"'{input_name}' references "
                        f"'{capability}.{output_name}', but provider "
                        f"'{provider_name}' does not declare output "
                        f"'{output_name}'"
                    )

                output_definition = provider_outputs[output_name]
                input_type = definition.get("type")
                output_type = output_definition.get("type")

                if input_type is None or output_type is None:
                    raise ValueError(
                        f"Plugin '{plugin_name}' input '{input_name}' "
                        f"and provider '{provider_name}' output "
                        f"'{output_name}' must declare types"
                    )

                compatible_types = {
                    "string": {"string"},
                    "integer": {"integer"},
                    "number": {"integer", "number"},
                    "boolean": {"boolean"},
                }

                if output_type not in compatible_types.get(input_type, set()):
                    raise ValueError(
                        f"Type mismatch for plugin '{plugin_name}' "
                        f"input '{input_name}': expects '{input_type}', "
                        f"but provider '{provider_name}' output "
                        f"'{output_name}' declares '{output_type}'"
                    )
