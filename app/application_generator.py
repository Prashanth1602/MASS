from pathlib import Path


class ApplicationGenerator:

    def generate(
        self,application_name: str, output_directory: Path, plugins: list[dict] ) -> list[str]:
        if plugins is None:
            plugins = []

        app_directory = output_directory / "app"

        app_directory.mkdir(
            parents=True,
            exist_ok=True
        )
        
        (app_directory / "__init__.py").touch()

        main_file = app_directory / "main.py"

        requirements_file = (output_directory / "requirements.txt")


        packages = {"fastapi", "uvicorn"}

        for plugin in plugins:
            packages.update(plugin.get("runtime_dependencies", []))

        requirements_file.write_text("\n".join(sorted(packages)) + "\n")

        dockerfile = output_directory / "Dockerfile"

        dockerfile.write_text(
    """FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
)
        imports = []
        registrations = []

        for plugin in plugins:
            if plugin.get("type") != "code":
                continue

            plugin_name = plugin["name"]
            router_name = f"{plugin_name}_router"

            imports.append(
                f"from app.{plugin_name}.router import "
                f"router as {router_name}"
            )

            registrations.append(
                f"app.include_router({router_name})"
            )

        imports_content = "\n".join(imports)
        registrations_content = "\n".join(registrations)

        main_content = f'''from fastapi import FastAPI
{imports_content}

app = FastAPI(
    title="{application_name} Application"
)

{registrations_content}


@app.get("/")
def root():
    return {{
        "message": "Generated application is running"
    }}
'''
        main_file.write_text(main_content)

        return [
            str(main_file)
        ]

