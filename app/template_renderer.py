class TemplateRenderer:

    def render(
        self,
        content: str,
        configuration: dict,
        schema: dict,
        inputs: dict
    ) -> str:

        # Render normal configuration
        for key, value in configuration.items():

            placeholder = (
                "{{ "
                + key
                + " }}"
            )

            if placeholder not in content:
                continue

            definition = schema.get(
                key,
                {}
            )

            if definition.get("secret", False):

                replacement = (
                    'os.getenv("'
                    + key.upper()
                    + '")'
                )

            else:

                replacement = str(value)

            content = content.replace(
                placeholder,
                replacement
            )

        # Render inputs
        for key, definition in inputs.items():

            placeholder = (
                "{{ input."
                + key
                + " }}"
            )

            if placeholder not in content:
                continue

            if definition.get("secret", False):

                # For now we use the input name.
                env_name = key.upper()

                replacement = (
                    'os.getenv("'
                    + env_name
                    + '")'
                )

            else:

                replacement = str(
                    definition["value"]
                )

            content = content.replace(
                placeholder,
                replacement
            )

        return content