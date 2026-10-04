import yaml


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

            # Ports
            if "ports" in plugin:
                service["ports"] = plugin["ports"]

            # Environment variables
            if "environment" in plugin:
                service["environment"] = plugin["environment"]

            # Volumes
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