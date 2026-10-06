class DependencyResolver:

    def resolve(self, plugins: list[dict]) -> dict:

        providers = {}

        for plugin in plugins:

            for capability in plugin.get("provides", []):

                providers.setdefault(
                    capability,
                    []
                ).append(plugin["name"])

        dependencies = {}

        for plugin in plugins:

            plugin_name = plugin["name"]

            dependencies[plugin_name] = {}

            for requirement in plugin.get("requires", []):

                matching_providers = providers.get(
                    requirement,
                    []
                )

                if not matching_providers:
                    raise ValueError(
                        f"Plugin '{plugin_name}' requires "
                        f"capability '{requirement}', "
                        f"but no selected plugin provides it"
                    )

                if len(matching_providers) > 1:
                    raise ValueError(
                        f"Plugin '{plugin_name}' requires "
                        f"capability '{requirement}', "
                        f"but multiple selected plugins provide it: "
                        f"{', '.join(matching_providers)}"
                    )

                dependencies[plugin_name][requirement] = (
                    matching_providers[0]
                )

        return dependencies