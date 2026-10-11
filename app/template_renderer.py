import re


class TemplateRenderer:
    PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

    def render(
        self,
        content: str,
        configuration: dict,
        schema: dict,
        inputs: dict,
        plugin_name: str = "plugin",
    ) -> str:

        def replace_placeholder(match):
            expression = match.group(1).strip()

            # Resolve plugin inputs, such as {{ input.database_host }}
            if expression.startswith("input."):
                input_name = expression[len("input."):]

                if input_name not in inputs:
                    raise ValueError(
                        f"Unresolved template input '{input_name}' "
                        f"in plugin '{plugin_name}'"
                    )

                definition = inputs[input_name]

                if definition.get("secret", False):
                    env_name = definition.get("secret_name")

                    if not env_name:
                        raise ValueError(
                            f"Secret input '{input_name}' in plugin "
                            f"'{plugin_name}' has no environment variable name"
                        )

                    return f'os.getenv({env_name!r})'

                if "value" not in definition:
                    raise ValueError(
                        f"Input '{input_name}' in plugin '{plugin_name}' "
                        "has no resolved value"
                    )

                return repr(definition["value"])

            # Resolve normal plugin configuration, such as {{ name }}
            if expression not in configuration:
                raise ValueError(
                    f"Unresolved configuration placeholder '{expression}' "
                    f"in plugin '{plugin_name}'"
                )

            value = configuration[expression]
            field_schema = schema.get(expression, {})

            if field_schema.get("secret", False):
                env_name = (
                    f"{plugin_name}_{expression}"
                ).upper()

                return f'os.getenv({env_name!r})'

            return repr(value)

        rendered = self.PLACEHOLDER_PATTERN.sub(
            replace_placeholder,
            content,
        )

        if "{{" in rendered or "}}" in rendered:
            raise ValueError(
                f"Malformed or unresolved template placeholder "
                f"in plugin '{plugin_name}'"
            )

        return rendered
