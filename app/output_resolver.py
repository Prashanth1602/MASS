class OutputResolver:

    def resolve(self, plugin: dict) -> dict:
        outputs = plugin.get("outputs", {})
        configuration = plugin.get("resolved_configuration", {})
        resolved_outputs = {}

        for name, definition in outputs.items():
            value = definition.get("value")

            if name == "host" and plugin.get("type") == "container":
                value = plugin["name"]

            elif isinstance(value, str):
                for key, config_value in configuration.items():
                    placeholder = "{{ " + key + " }}"
                    value = value.replace(placeholder, str(config_value))

            resolved_outputs[name] = {
                "value": value,
                "secret": definition.get("secret", False)
            }

            if resolved_outputs[name]["secret"]:
                resolved_outputs[name]["secret_name"] = (
                    plugin["name"].upper() + "_" + name.upper()
                )

        return resolved_outputs
