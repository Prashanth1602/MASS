from pathlib import Path
import shutil
from urllib import response

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from app import main as app_module
from app.main import app
from app.plugin_registry import PluginRegistry
from app.plugin_scaffolder import PluginScaffolder


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)

TEST_APP_NAME = "pytest_integration_app"
TEST_SECRET = "integration-test-secret"


@pytest.fixture
def generated_output(monkeypatch):
    monkeypatch.chdir(ROOT)

    output_dir = ROOT / "generated" / TEST_APP_NAME
    shutil.rmtree(output_dir, ignore_errors=True)

    yield output_dir

    shutil.rmtree(output_dir, ignore_errors=True)


def valid_payload():
    return {
        "application": {
            "name": TEST_APP_NAME
        },
        "plugins": {
            "postgres": {
                "database": "movie_db",
                "username": "movie_user",
                "password": TEST_SECRET,
            },
            "redis": {},
            "authentication": {
                    "jwt_secret": "integration-test-secret-key-at-least-32-bytes"
                },
        },
    }


def test_build_generates_application_files(generated_output):
    response = client.post("/build", json=valid_payload())

    assert response.status_code == 200
    assert response.json()["message"] == "Application generated successfully"

    expected_files = [
        "app/main.py",
        "app/authentication/auth.py",
        "app/authentication/config.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".env",
        ".gitignore",
    ]

    for relative_path in expected_files:
        assert (generated_output / relative_path).is_file(), (
            f"Missing generated file: {relative_path}"
        )

    requirements = (generated_output / "requirements.txt").read_text()
    assert "fastapi" in requirements
    assert "uvicorn" in requirements
    assert "redis" in requirements
    assert "psycopg[binary]" in requirements


def test_build_rejects_unknown_plugin():
    payload = {
        "application": {"name": "unknown_plugin_test"},
        "plugins": {"plugin_that_does_not_exist": {}},
    }

    response = client.post("/build", json=payload)

    assert response.status_code == 404
    assert "detail" in response.json()
    assert "not found" in response.json()["detail"].lower()


def test_build_rejects_invalid_plugin_configuration():
    payload = {
        "application": {"name": "invalid_config_test"},
        "plugins": {
            "postgres": {
                "unexpected_option": "value",
            }
        },
    }

    response = client.post("/build", json=payload)

    assert response.status_code == 400
    assert "detail" in response.json()


def test_build_does_not_expose_secret(generated_output):
    response = client.post("/build", json=valid_payload())

    assert response.status_code == 200
    assert response.json()["message"] == "Application generated successfully"

    assert TEST_SECRET not in response.text

    env_content = (generated_output / ".env").read_text()
    assert f"POSTGRES_PASSWORD={TEST_SECRET}" in env_content

    config_content = (
        generated_output / "app" / "authentication" / "config.py"
    ).read_text()
 
    assert TEST_SECRET not in config_content
    assert "os.getenv('POSTGRES_PASSWORD')" in config_content 

    compose_content = (
        generated_output / "docker-compose.yml"
    ).read_text()

    assert "${POSTGRES_PASSWORD}" in compose_content
    assert TEST_SECRET not in compose_content


def test_build_rejects_provider_missing_required_output():
    payload = {
        "application": {
            "name": "missing_output_test"
        },
        "plugins": {
            "postgres": {
                "database": "movie_db",
                "username": "movie_user",
                "password": "integration-test-secret",
            },
            "redis": {},
            "authentication": {
                    "jwt_secret": "integration-test-secret-key-at-least-32-bytes"
                },
        },
    }

    postgres = app_module.registry.get("postgres")
    assert postgres is not None, "Postgres plugin should be registered"
    original_outputs = postgres["outputs"]

    try:
        postgres["outputs"] = {
            key: value
            for key, value in original_outputs.items()
            if key != "password"
        }

        response = client.post("/build", json=payload)

        assert response.status_code == 400
        assert "does not declare output 'password'" in response.json()["detail"]

    finally:
        postgres["outputs"] = original_outputs


def test_build_rejects_invalid_configuration_type(generated_output):
    payload = valid_payload()
    payload["plugins"]["postgres"]["port"] = "not-a-port"

    response = client.post("/build", json=payload)

    assert response.status_code == 400
    assert "expected integer" in response.json()["detail"]
    assert not generated_output.exists()


def test_build_rejects_existing_application(generated_output):
    response = client.post("/build", json=valid_payload())

    assert response.status_code == 200
    assert response.json()["message"] == "Application generated successfully"

    original_main = (
        generated_output / "app" / "main.py"
    ).read_text()

    second_response = client.post("/build", json=valid_payload())

    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["detail"]

    assert (
        generated_output / "app" / "main.py"
    ).read_text() == original_main


def test_build_cleans_staging_directory_after_failure(
    generated_output,
    monkeypatch,
):
    def fail_generation(*args, **kwargs):
        raise RuntimeError("Simulated generation failure")

    monkeypatch.setattr(
        app_module.code_generator,
        "generate",
        fail_generation,
    )

    response = client.post("/build", json=valid_payload())

    assert response.status_code == 500
    assert "generation failed" in response.json()["detail"].lower()
    assert not generated_output.exists()

    staging_directories = list(
        generated_output.parent.glob(
            f".{TEST_APP_NAME}.staging-*"
        )
    )
    assert staging_directories == []



def test_concurrent_build_for_same_name_returns_conflict(generated_output, monkeypatch):
    entered_generation = Event()
    release_generation = Event()

    original_generate = app_module.code_generator.generate

    def slow_generate(plugin, output_directory):
        entered_generation.set()

        if not release_generation.wait(timeout=10):
            raise RuntimeError("Timed out waiting to release generation")

        return original_generate(plugin, output_directory)

    monkeypatch.setattr(app_module.code_generator, "generate", slow_generate)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(
            client.post,
            "/build",
            json=valid_payload(),
        )

        try:
            assert entered_generation.wait(timeout=5), ("First build did not reach code generation")

            second_response = client.post(
                "/build",
                json=valid_payload(),
            )

            assert second_response.status_code == 409
            assert "already in progress" in (
                second_response.json()["detail"].lower()
            )

        finally:
            release_generation.set()

        first_response = first_future.result(timeout=15)

    assert first_response.status_code == 200
    assert first_response.json()["message"] == ("Application generated successfully")
    assert generated_output.is_dir()
    assert (generated_output / "docker-compose.yml").is_file()


def test_build_releases_lock_after_generation_failure(generated_output,monkeypatch):
    original_generate = app_module.code_generator.generate

    def fail_generation(*args, **kwargs):
        raise RuntimeError("Simulated generation failure")

    monkeypatch.setattr(app_module.code_generator, "generate", fail_generation)

    failed_response = client.post(
        "/build",
        json=valid_payload(),
    )

    assert failed_response.status_code == 500
    assert not generated_output.exists()

    monkeypatch.setattr(app_module.code_generator, "generate", original_generate)

    retry_response = client.post(
        "/build",
        json=valid_payload(),
    )

    assert retry_response.status_code == 200
    assert (retry_response.json()["message"] == "Application generated successfully")
    assert generated_output.is_dir()
    assert (generated_output / "docker-compose.yml").is_file()


def test_build_logs_internal_error_without_exposing_it(generated_output, monkeypatch, caplog):
    import logging

    def fail_generation(*args, **kwargs):
        raise RuntimeError("internal-sensitive-debug-detail")

    monkeypatch.setattr(
        app_module.code_generator,
        "generate",
        fail_generation,
    )

    with caplog.at_level(logging.ERROR, logger="mass"):
        response = client.post(
            "/build",
            json=valid_payload(),
        )

    assert response.status_code == 500
    assert "internal-sensitive-debug-detail" not in response.text
    assert "internal-sensitive-debug-detail" in caplog.text
    assert "Application generation failed" in caplog.text
    assert not generated_output.exists()


def test_build_registers_selected_hello_router(generated_output):
    payload = {
        "application": {"name": TEST_APP_NAME},
        "plugins": {
            "hello": {"name": "MASS"},
        },
    }

    response = client.post("/build", json=payload)

    assert response.status_code == 200

    main_content = (
        generated_output / "app" / "main.py"
    ).read_text()

    router_content = (
        generated_output / "app" / "hello" / "router.py"
    ).read_text()

    assert (
        "from app.hello.router import router as hello_router"
        in main_content
    )
    assert "app.include_router(hello_router)" in main_content
    assert '@router.get("/")' in router_content



def test_build_api_with_freshly_scaffolded_plugin(tmp_path, monkeypatch):
    # Create a fresh plugin outside the project's real plugins directory.
    plugins_directory = tmp_path / "plugins"
    scaffolder = PluginScaffolder(plugins_directory)
    scaffolder.create("fresh_greeting")

    # Load the new plugin through the real registry.
    test_registry = PluginRegistry(str(plugins_directory))
    test_registry.load_plugins()

    # Route the existing API service to this isolated registry.
    monkeypatch.setattr(app_module, "registry", test_registry)
    monkeypatch.setattr(
        app_module,
        "application_service",
        app_module.ApplicationService(test_registry),
    )

    # Keep generated output isolated from the real project.
    generated_directory = tmp_path / "generated"
    monkeypatch.chdir(tmp_path)

    payload = {
        "application": {
            "name": "fresh-greeting-app",
            "host_port": 8012,
        },
        "plugins": {
            "fresh_greeting": {},
        },
    }

    response = client.post("/build", json=payload)

    assert response.status_code == 200, response.text
    assert response.json()["application"] == "fresh-greeting-app"

    app_directory = (
        generated_directory / "fresh-greeting-app" / "app"
    )

    router_file = app_directory / "fresh_greeting" / "router.py"
    service_file = app_directory / "fresh_greeting" / "service.py"
    main_file = app_directory / "main.py"

    assert router_file.is_file()
    assert service_file.is_file()
    assert main_file.is_file()

    main_content = main_file.read_text(encoding="utf-8")
    assert (
        "from app.fresh_greeting.router import "
        "router as fresh_greeting_router"
    ) in main_content
    assert "app.include_router(fresh_greeting_router)" in main_content

    service_content = service_file.read_text(encoding="utf-8")
    assert "Hello from fresh_greeting!" in service_content
    assert "{{ message }}" not in service_content

    # Confirm that generated Python files have valid syntax.
    for python_file in app_directory.rglob("*.py"):
        compile(
            python_file.read_text(encoding="utf-8"),
            str(python_file),
            "exec",
        )





