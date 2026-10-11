from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import app


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
            "authentication": {},
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

    assert response.status_code == 200
    assert "error" in response.json()
    assert "not found" in response.json()["error"].lower()


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

    assert response.status_code == 200
    assert "error" in response.json()


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
    assert 'os.getenv("POSTGRES_PASSWORD")' in config_content

    compose_content = (
        generated_output / "docker-compose.yml"
    ).read_text()

    assert "${POSTGRES_PASSWORD}" in compose_content
    assert TEST_SECRET not in compose_content
