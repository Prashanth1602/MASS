from pathlib import Path

from app.template_renderer import TemplateRenderer

class CodePluginGenerator:

    def __init__(self, plugins_directory: str = "plugins"):
        self.plugins_directory = Path(plugins_directory)
        self.renderer = TemplateRenderer()

    def generate(self, plugin: dict, output_directory: Path) -> list[str]:
        plugin_name = plugin["name"]

        plugin_directory = self.plugins_directory / plugin_name
        templates_directory = plugin_directory / "templates"

        if not templates_directory.is_dir():
            raise ValueError(
                f"Templates directory not found for code plugin "
                f"'{plugin_name}'"
            )

        router_template = templates_directory / "router.py"

        if not router_template.is_file():
            raise ValueError(
                f"Code plugin '{plugin_name}' is missing its required "
                f"entry point: templates/router.py"
            )

        configuration = plugin.get("resolved_configuration", {})
        schema = plugin.get("configuration", {})
        inputs = plugin.get("resolved_inputs", {})

        rendered_files = []

        for template_file in sorted(templates_directory.rglob("*")):
            if not template_file.is_file():
                continue

            relative_path = template_file.relative_to(templates_directory)
            output_file = (
                output_directory / "app" / plugin_name / relative_path
            )

            content = template_file.read_text(encoding="utf-8")

            try:
                content = self.renderer.render(
                    content=content,
                    configuration=configuration,
                    schema=schema,
                    inputs=inputs,
                    plugin_name=plugin_name,
                )
            except ValueError as exc:
                raise ValueError(
                    f"Template rendering failed for plugin "
                    f"'{plugin_name}', file '{relative_path}': {exc}"
                ) from exc

            if output_file.suffix == ".py":
                try:
                    compile(content, str(relative_path), "exec")
                except SyntaxError as exc:
                    raise ValueError(
                        f"Invalid Python syntax in code plugin "
                        f"'{plugin_name}', file '{relative_path}', "
                        f"line {exc.lineno}: {exc.msg}"
                    ) from exc

            rendered_files.append((output_file, content))

        generated_files = []

        plugin_output_directory = output_directory / "app" / plugin_name
        plugin_output_directory.mkdir(parents=True, exist_ok=True)

        init_file = plugin_output_directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        generated_files.append(str(init_file))

        for output_file, content in rendered_files:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(content, encoding="utf-8")
            generated_files.append(str(output_file))

        return generated_files

     
    def validate(self, plugin: dict) -> None:
        plugin_name = plugin["name"]

        plugin_directory = self.plugins_directory / plugin_name
        templates_directory = plugin_directory / "templates"

        if not templates_directory.is_dir():
            raise ValueError(
                f"Templates directory not found for code plugin "
                f"'{plugin_name}'"
            )

        if not (templates_directory / "router.py").is_file():
            raise ValueError(
                f"Code plugin '{plugin_name}' is missing its required "
                f"entry point: templates/router.py"
            )

        configuration = plugin.get("resolved_configuration", {})
        schema = plugin.get("configuration", {})
        inputs = plugin.get("resolved_inputs", {})

        for template_file in sorted(templates_directory.rglob("*")):
            if not template_file.is_file():
                continue

            relative_path = template_file.relative_to(templates_directory)

            try:
                content = self.renderer.render(
                    content=template_file.read_text(encoding="utf-8"),
                    configuration=configuration,
                    schema=schema,
                    inputs=inputs,
                    plugin_name=plugin_name,
                )
            except ValueError as exc:
                raise ValueError(
                    f"Template validation failed for plugin "
                    f"'{plugin_name}', file '{relative_path}': {exc}"
                ) from exc

            if template_file.suffix == ".py":
                try:
                    compile(content, str(relative_path), "exec")
                except SyntaxError as exc:
                    raise ValueError(
                        f"Invalid Python syntax in code plugin "
                        f"'{plugin_name}', file '{relative_path}', "
                        f"line {exc.lineno}: {exc.msg}"
                    ) from exc

