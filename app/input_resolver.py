class InputResolver:

    def resolve(self, plugin: dict, dependencies: dict, resolved_plugins: dict) -> dict:

        inputs = plugin.get("inputs", {})

        resolved_inputs = {}

        for input_name, definition in inputs.items():

            source = definition["from"]

            capability, output_name = (source.split(".", 1))

            provider_name = dependencies[plugin["name"]][capability]

            provider = resolved_plugins[provider_name]

            outputs = provider.get(
                "resolved_outputs",
                {}
            )

            if output_name not in outputs:

                raise ValueError(
                    f"Plugin '{provider_name}' "
                    f"does not provide output "
                    f"'{output_name}'"
                )

            output = outputs[output_name]

            resolved_inputs[input_name] = {
                            "value": output["value"],
                            "secret": output.get("secret", False)
                        }

        return resolved_inputs