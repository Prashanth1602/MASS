import re

class PluginConformanceValidator:
    PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

    TYPE_CHECKS = {
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: type(value) is int,
        "number": lambda value: type(value) in (int, float),
        "boolean": lambda value: type(value) is bool,
    }

    def validate(self, plugin: dict) -> None:
        plugin_name = plugin.get("name", "unknown")

        self._validate_unique_strings(plugin_name, "provides", plugin.get("provides", []))
        self._validate_unique_strings(plugin_name, "requires", plugin.get("requires", []))
        self._validate_configuration(plugin)
        self._validate_runtime_dependencies(plugin)
        self._validate_environment(plugin)
        self._validate_inputs(plugin)

    def _validate_unique_strings(self, plugin_name: str, field_name: str, values: list) -> None:
        if not isinstance(values, list):
            raise ValueError(
                f"Plugin '{plugin_name}' field '{field_name}' "
                "must be a list"
            )

        seen = set()

        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Plugin '{plugin_name}' field '{field_name}' "
                    "must contain non-empty strings"
                )

            if value in seen:
                raise ValueError(
                    f"Plugin '{plugin_name}' declares duplicate "
                    f"'{field_name}' entry '{value}'"
                )

            seen.add(value)

    def _validate_configuration(self, plugin: dict) -> None:
        plugin_name = plugin.get("name", "unknown")

        for key, definition in plugin.get("configuration", {}).items():
            expected_type = definition.get("type")
            check_type = self.TYPE_CHECKS.get(expected_type)

            if check_type is None:
                raise ValueError(
                    f"Plugin '{plugin_name}' configuration '{key}' "
                    f"has unsupported type '{expected_type}'"
                )

            if "default" in definition:
                default = definition["default"]

                if not check_type(default):
                    raise ValueError(
                        f"Plugin '{plugin_name}' configuration '{key}' "
                        f"has a default of the wrong type; "
                        f"expected {expected_type}, "
                        f"got {type(default).__name__}"
                    )

    def _validate_runtime_dependencies(self, plugin: dict) -> None:
        plugin_name = plugin.get("name", "unknown")
        dependencies = plugin.get("runtime_dependencies", [])

        if not isinstance(dependencies, list):
            raise ValueError(
                f"Plugin '{plugin_name}' runtime_dependencies "
                "must be a list"
            )

        seen = set()

        for dependency in dependencies:
            if not isinstance(dependency, str) or not dependency.strip():
                raise ValueError(
                    f"Plugin '{plugin_name}' runtime dependencies "
                    "must be non-empty strings"
                )

            if dependency in seen:
                raise ValueError(
                    f"Plugin '{plugin_name}' declares duplicate "
                    f"runtime dependency '{dependency}'"
                )

            seen.add(dependency)

    def _validate_environment(self, plugin: dict) -> None:
        plugin_name = plugin.get("name", "unknown")
        configuration = plugin.get("configuration", {})

        for env_name, value in plugin.get("environment", {}).items():
            if not isinstance(value, str):
                raise ValueError(
                    f"Plugin '{plugin_name}' environment variable "
                    f"'{env_name}' must have a string value"
                )

            for match in self.PLACEHOLDER_PATTERN.finditer(value):
                key = match.group(1).strip()

                if key not in configuration:
                    raise ValueError(
                        f"Plugin '{plugin_name}' environment variable "
                        f"'{env_name}' references unknown configuration "
                        f"key '{key}'"
                    )

            remainder = self.PLACEHOLDER_PATTERN.sub("", value)

            if "{{" in remainder or "}}" in remainder:
                raise ValueError(
                    f"Plugin '{plugin_name}' environment variable "
                    f"'{env_name}' contains a malformed placeholder"
                )

    def _validate_inputs(self, plugin: dict) -> None:
        plugin_name = plugin.get("name", "unknown")

        for input_name, definition in plugin.get("inputs", {}).items():
            source = definition.get("from")

            if (
                not isinstance(source, str)
                or source.count(".") != 1
                or any(not part.strip() for part in source.split("."))
            ):
                raise ValueError(
                    f"Plugin '{plugin_name}' input '{input_name}' "
                    "must reference an output using "
                    "'capability.output' format"
                )
