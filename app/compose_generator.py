from fastapi import dependencies
import yaml

def resolve_template(value: str, configuration: dict):
        if not isinstance(value, str):
            return value

        for key, config_value in configuration.items():
            placeholder = f"{{{{ {key} }}}}"
            value = value.replace(placeholder, str(config_value))

        return value

def resolve_environment_value(value: str, configuration: dict, schema: dict, plugin_name: str):

    if not isinstance(value, str):
        return value

    for key, config_value in configuration.items():
        placeholder = f"{{{{ {key} }}}}"

        if placeholder not in value:
            continue

        definition = schema.get(key, {})

        if definition.get("secret", False):
            env_name = f"{plugin_name.upper()}_{key.upper()}"
            value = value.replace(placeholder, "${" + env_name + "}")

        else:
            value = value.replace(placeholder, str(config_value))

    return value

class ComposeGenerator:

    def generate( self, application_name: str, plugins: list[dict], runtime_dependencies: dict, host_port: int = 8000) -> str:

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
                    environment[key] = resolve_environment_value(value, configuration, plugin.get("configuration", {}), plugin["name"])

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

        app_dependencies = sorted({ dependency for dependencies in runtime_dependencies.values() for dependency in dependencies})

        services["app"] = self.build_application_service(app_dependencies, host_port) 

        return yaml.safe_dump(
            compose,
            sort_keys=False
        )

    
    def generate_env_file(self, plugins: list[dict]) -> str:
        from urllib.parse import quote

        lines = []

        postgres_plugin = next(
            (
                plugin for plugin in plugins
                if plugin["name"] == "postgres"
            ),
            None,
        )

        if postgres_plugin:
            configuration = postgres_plugin.get(
                "resolved_configuration", {}
            )

            database = configuration.get("database", "app")
            username = configuration.get("username", "app")
            password = configuration.get("password", "")
            port = configuration.get("port", 5432)

            lines.extend([
                "POSTGRES_HOST=postgres",
                f"POSTGRES_PORT={port}",
                f"POSTGRES_DB={database}",
                f"POSTGRES_USER={username}",
            ])

            for plugin in plugins:
                plugin_name = plugin["name"].upper()
                plugin_configuration = plugin.get(
                    "resolved_configuration", {}
                )
                schema = plugin.get("configuration", {})

                for key, value in plugin_configuration.items():
                    definition = schema.get(key, {})

                    if definition.get("secret", False):
                        env_name = f"{plugin_name}_{key.upper()}"
                        lines.append(f"{env_name}={value}")

            encoded_username = quote(str(username), safe="")
            encoded_password = quote(str(password), safe="")

            lines.append(
                "DATABASE_URL="
                f"postgresql+psycopg://{encoded_username}:"
                f"{encoded_password}@postgres:{port}/{database}"
            )

        return "\n".join(lines) + "\n"   
    
    def build_application_service(self, dependencies: list[str], host_port: int = 8000,) -> dict:
        service = {
            "build": ".",
            "ports": [f"{host_port}:8000"],
            "env_file": [".env"],
            "volumes": [
                "./alembic:/app/alembic",
                "./alembic.ini:/app/alembic.ini",
           ],
        }

        if dependencies:
            service["depends_on"] = dependencies

        return service


