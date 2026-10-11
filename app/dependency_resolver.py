class DependencyResolver:

    def resolve(self, plugins: list[dict]) -> dict:
        providers = {}

        for plugin in plugins:
            for capability in plugin.get("provides", []):
                providers.setdefault(capability, []).append(
                    plugin["name"]
                )

        dependencies = {}

        for plugin in plugins:
            plugin_name = plugin["name"]
            dependencies[plugin_name] = {}

            for requirement in plugin.get("requires", []):
                matching_providers = providers.get(requirement, [])

                if not matching_providers:
                    raise ValueError(
                        f"Plugin '{plugin_name}' requires "
                        f"capability '{requirement}', "
                        "but no selected plugin provides it"
                    )

                if len(matching_providers) > 1:
                    raise ValueError(
                        f"Plugin '{plugin_name}' requires "
                        f"capability '{requirement}', "
                        "but multiple selected plugins provide it: "
                        f"{', '.join(matching_providers)}"
                    )

                provider_name = matching_providers[0]

                if provider_name == plugin_name:
                    raise ValueError(
                        f"Plugin '{plugin_name}' cannot satisfy "
                        f"its own requirement '{requirement}'"
                    )

                dependencies[plugin_name][requirement] = provider_name

        self._validate_dependency_cycles(dependencies)

        return dependencies

    @staticmethod
    def _validate_dependency_cycles(dependencies: dict) -> None:
        graph = {
            plugin_name: list(
                resolved.values()
            )
            for plugin_name, resolved in dependencies.items()
        }

        state = {name: 0 for name in graph}
        path = []

        def visit(plugin_name: str) -> None:
            state[plugin_name] = 1
            path.append(plugin_name)

            for provider_name in graph[plugin_name]:
                if state[provider_name] == 1:
                    cycle_start = path.index(provider_name)
                    cycle = path[cycle_start:] + [provider_name]

                    raise ValueError(
                        "Dependency cycle detected: "
                        + " -> ".join(cycle)
                    )

                if state[provider_name] == 0:
                    visit(provider_name)

            path.pop()
            state[plugin_name] = 2

        for plugin_name in graph:
            if state[plugin_name] == 0:
                visit(plugin_name)
