class RuntimeDependencyResolver:

    def resolve(
        self,
        dependencies: dict,
        plugins: list[dict]
    ) -> dict:

        plugin_types = {
            plugin["name"]: plugin["type"]
            for plugin in plugins
        }

        runtime_dependencies = {}

        for plugin_name, requirements in dependencies.items():

            if plugin_types.get(plugin_name) != "code":
                continue

            service_dependencies = set()

            for provider_name in requirements.values():

                if isinstance(provider_name, list):
                    provider_names = provider_name
                else:
                    provider_names = [provider_name]

                for provider in provider_names:

                    if plugin_types.get(provider) == "container":
                        service_dependencies.add(provider)

            runtime_dependencies[plugin_name] = sorted(
                service_dependencies
            )

        return runtime_dependencies