from pathlib import Path

class CodePluginGenerator:

    def generate(self, plugin: dict, output_directory: Path) -> list[str]:

        plugin_directory = Path("plugins") / plugin["name"]

        templates_directory = (
            plugin_directory / "templates"
        )

        if not templates_directory.exists():

            raise ValueError(
                f"Templates directory not found for "
                f"code plugin '{plugin['name']}'"
            )

        generated_files = []

        for template_file in templates_directory.rglob("*"):

            if not template_file.is_file():
                continue

            relative_path = (template_file.relative_to(templates_directory))

            output_file = (output_directory / relative_path)

            output_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            content = template_file.read_text()

            output_file.write_text(content)

            generated_files.append(
                str(output_file)
            )

        return generated_files