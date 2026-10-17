from pathlib import Path

import pytest

from app.code_plugin_generator import CodePluginGenerator


def create_plugin(tmp_path, files):
    plugin_name = "test_plugin"
    templates = tmp_path / "plugins" / plugin_name / "templates"
    templates.mkdir(parents=True)

    for filename, content in files.items():
        path = templates / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    return plugin_name, templates


def test_rejects_missing_router(tmp_path, monkeypatch):
    plugin_name, _ = create_plugin(
        tmp_path,
        {"hello.py": 'def greet():\n    return "Hello"\n'},
    )
    monkeypatch.chdir(tmp_path)

    generator = CodePluginGenerator()

    with pytest.raises(ValueError, match="templates/router.py"):
        generator.generate(
            {"name": plugin_name},
            tmp_path / "generated",
        )


def test_rejects_invalid_python_syntax(tmp_path, monkeypatch):
    plugin_name, _ = create_plugin(
        tmp_path,
        {
            "router.py": "router = None\n",
            "broken.py": "def broken(:\n    pass\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    output_directory = tmp_path / "generated"
    generator = CodePluginGenerator()

    with pytest.raises(ValueError, match="Invalid Python syntax"):
        generator.generate(
            {"name": plugin_name},
            output_directory,
        )

    assert not (output_directory / "app" / plugin_name / "router.py").exists()


def test_generates_valid_python_files(tmp_path, monkeypatch):
    plugin_name, _ = create_plugin(
        tmp_path,
        {
            "router.py": "router = None\n",
            "hello.py": 'def greet():\n    return "Hello"\n',
        },
    )
    monkeypatch.chdir(tmp_path)

    output_directory = tmp_path / "generated"
    generator = CodePluginGenerator()

    generated_files = generator.generate(
        {"name": plugin_name},
        output_directory,
    )

    router_file = output_directory / "app" / plugin_name / "router.py"
    hello_file = output_directory / "app" / plugin_name / "hello.py"

    assert router_file.exists()
    assert hello_file.exists()
    assert str(router_file) in generated_files
    assert str(hello_file) in generated_files
