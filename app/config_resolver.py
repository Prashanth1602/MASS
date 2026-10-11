
class ConfigResolver:
    TYPE_CHECKS = {
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: type(value) is int,
        "number": lambda value: type(value) in (int, float),
        "boolean": lambda value: type(value) is bool,
    }

    def resolve(self, plugin: dict, user_config: dict) -> dict:
        plugin_name = plugin.get("name", "unknown")
        schema = plugin.get("configuration", {})
        resolved = {}

        for key in user_config:
            if key not in schema:
                raise ValueError(
                    f"Unknown configuration key: '{key}' "
                    f"for plugin '{plugin_name}'"
                )

        for key, definition in schema.items():
            if key in user_config:
                value = user_config[key]
            elif "default" in definition:
                value = definition["default"]
            elif definition.get("required", False):
                raise ValueError(
                    f"Missing required configuration key: '{key}' "
                    f"for plugin '{plugin_name}'"
                )
            else:
                continue

            expected_type = definition.get("type")

            if expected_type not in self.TYPE_CHECKS:
                raise ValueError(
                    f"Unsupported configuration type '{expected_type}' "
                    f"for '{key}' in plugin '{plugin_name}'"
                )

            if not self.TYPE_CHECKS[expected_type](value):
                raise ValueError(
                    f"Invalid type for configuration key '{key}' "
                    f"in plugin '{plugin_name}': expected "
                    f"{expected_type}, got {type(value).__name__}"
                )

            resolved[key] = value

        return resolved

    def get_secret_fields(self, plugin: dict, resolved_configuration: dict) -> dict:
        schema = plugin.get("configuration", {})
        secrets = {}

        for key, value in resolved_configuration.items():
            definition = schema.get(key, {})

            if definition.get("secret", False):
                secrets[key] = value

        return secrets
