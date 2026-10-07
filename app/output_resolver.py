class OutputResolver:

    def resolve(self, plugin: dict) -> dict:

        outputs = plugin.get("outputs", {})

        configuration = plugin.get("resolved_configuration", {})

        resolved_outputs = {}

        for name, definition in outputs.items():

            value = definition.get("value")

            if isinstance(value, str):

                for key, config_value in configuration.items():

                    placeholder = ("{{ " + key + " }}")

                    value = value.replace(placeholder, str(config_value))

            resolved_outputs[name] = {
                "value": value,
                "secret": definition.get("secret", False)
            }

            output_data = { "value": value, "secret": definition.get("secret", False)}

            if output_data["secret"]:
                output_data["secret_name"] = (plugin["name"].upper() + "_" + name.upper())

        return resolved_outputs