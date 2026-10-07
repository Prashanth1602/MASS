from pathlib import Path

from app.template_renderer import TemplateRenderer


class CodePluginGenerator:

      def __init__(self):
          self.renderer = TemplateRenderer()

      def generate(self, plugin: dict, output_directory: Path) -> list[str]:

        plugin_directory = (Path("plugins") / plugin["name"])

        templates_directory = (plugin_directory / "templates")

        if not templates_directory.exists():

            raise ValueError(
                f"Templates directory not found for "
                f"code plugin '{plugin['name']}'"
            )

        generated_files = []

        configuration = plugin.get("resolved_configuration", {})

        schema = plugin.get("configuration", {})

        for template_file in templates_directory.rglob("*"):

            if not template_file.is_file():
                continue

            relative_path = (template_file.relative_to(templates_directory))

            output_file = (output_directory / plugin["name"] / relative_path)

            output_file.parent.mkdir(parents=True,exist_ok=True)

            content = template_file.read_text()

            inputs = plugin.get("resolved_inputs", {})

            content = self.renderer.render(content, configuration, schema, inputs)

            output_file.write_text(content)

            generated_files.append(str(output_file))

        return generated_files