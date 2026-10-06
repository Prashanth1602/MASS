class ConfigResolver:

    def resolve(self, plugin: dict, user_config: dict) -> dict:

        schema = plugin.get("configuration", {})
        resolved = {}

        for key in user_config:
            if key not in schema:
                raise ValueError(
                    f"Unknown configuration key: '{key}' for plugin '{plugin.get('name', 'unknown')}'"
                )

            resolved[key] = user_config[key]

        for key, definition in schema.items():
            if key not in resolved:
                if "default" in definition:
                    resolved[key] = definition["default"]
                elif definition.get("required", False):
                    raise ValueError(
                        f"Missing required configuration key: '{key}' for plugin '{plugin.get('name', 'unknown')}'"
                    )

        return resolved

    def get_secret_fields(self, plugin: dict, resolved_configuration: dict) -> dict:
        schema = plugin.get("configuration", {})
        secrets = {}

        for key, value in resolved_configuration.items():
            definition = schema.get(key, {})

            if definition.get("secret", False):
                secrets[key] = value

        return secrets