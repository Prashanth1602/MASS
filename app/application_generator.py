from pathlib import Path

from app.database_generator import DatabaseGenerator
from app.migration_generator import MigrationGenerator


class ApplicationGenerator:

    def __init__(self):
        self.database_generator = DatabaseGenerator()
        self.migration_generator = MigrationGenerator()

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

        uses_database = any("database" in plugin.get("provides", {})
                            for plugin in plugins
            )

        if uses_database:
            self.database_generator.generate(output_directory)
            self.migration_generator.generate(output_directory, plugins=plugins)
            packages.add("sqlalchemy")
            packages.add("alembic")

        requirements_file.write_text("\n".join(sorted(packages)) + "\n")

        dockerfile = output_directory / "Dockerfile"

        dockerfile.write_text(
    """FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

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

        database_health_import = ""
        database_health_endpoint = ""

        uses_database = any(
                "database" in plugin.get("provides", [])
                for plugin in plugins
            )

        if uses_database:
            database_health_import = """
from sqlalchemy import text
from app.core.database import engine
"""

        database_health_endpoint = '''

@app.get("/health/database")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "connected"}
'''

        main_content = f'''from fastapi import FastAPI
{imports_content}
{database_health_import}

app = FastAPI(
    title="{application_name} Application"
)
{registrations_content}
{database_health_endpoint}

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

