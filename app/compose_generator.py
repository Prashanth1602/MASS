import yaml

def resolve_template(value: str, configuration: dict):
        if not isinstance(value, str):
            return value

        for key, config_value in configuration.items():
            placeholder = f"{{{{ {key} }}}}"
            value = value.replace(placeholder, str(config_value))

        return value

def resolve_environment_value(value: str, configuration: dict, schema: dict):

    if not isinstance(value, str):
        return value

    for key, config_value in configuration.items():
        placeholder = f"{{{{ {key} }}}}"

        if placeholder not in value:
            continue

        definition = schema.get(key, {})

        if definition.get("secret", False):
            value = value.replace(placeholder, "${" + key + "}")

        else:
            value = value.replace(placeholder, str(config_value))

    return value

class ComposeGenerator:

    def generate( self, application_name: str, plugins: list[dict]) -> str:

        services = {}
        volumes = {}

        for plugin in plugins:

            if plugin["type"] != "container":
                continue

            image = plugin["image"]

            service: dict[str, object] = {
                "image": f'{image["repository"]}:{image["tag"]}'
            }

            if "ports" in plugin:
                service["ports"] = plugin["ports"]

            if "environment" in plugin:

                configuration = plugin.get("resolved_configuration", {})

                environment = {}

                for key, value in plugin["environment"].items():
                    environment[key] = resolve_environment_value(value, configuration, plugin.get("configuration", {}))

                service["environment"] = environment

            if "volumes" in plugin:

                service_volumes = []

                for volume in plugin["volumes"]:

                    volume_name = volume["name"]
                    target = volume["target"]

                    service_volumes.append(
                        f"{volume_name}:{target}"
                    )

                    volumes[volume_name] = {}

                service["volumes"] = service_volumes

            services[plugin["name"]] = service

        compose = {
            "services": services
        }

        if volumes:
            compose["volumes"] = volumes

        return yaml.safe_dump(
            compose,
            sort_keys=False
        )

    def generate_env_file(self, plugins: list[dict]) -> str:
        lines = []

        for plugin in plugins:

            plugin_name = plugin["name"].upper()

            configuration = plugin.get("resolved_configuration", {})

            schema = plugin.get("configuration", {})
            
            for key, value in configuration.items():

                definition = schema.get(key, {})

                if definition.get("secret", False):

                    env_name = f"{plugin_name}_{key.upper()}"

                    lines.append(f"{env_name}={value}")

        return "\n".join(lines) + "\n"
