from pathlib import Path

import pytest

from app.plugin_registry import PluginRegistry


ROOT = Path(__file__).resolve().parents[1]


def write_plugin(directory: Path, content: str):
    plugin_dir = directory / "sample"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(content, encoding="utf-8")
    return plugin_dir


def test_all_existing_plugins_load_successfully():
    registry = PluginRegistry(str(ROOT / "plugins"))

    registry.load_plugins()

    assert {
        "postgres",
        "redis",
        "mysql",
        "hello",
        "authentication",
    }.issubset(set(registry.plugins))


def test_valid_code_plugin_loads(tmp_path):
    write_plugin(tmp_path,
        """
name: sample
version: "1.0"
type: code
provides:
  - greeting
""",
    )

    registry = PluginRegistry(str(tmp_path))
    registry.load_plugins()

    sample_plugin = registry.get("sample")
    assert sample_plugin is not None
    assert sample_plugin["type"] == "code"


def test_missing_required_field_is_rejected(tmp_path):
    write_plugin( tmp_path,
        """
version: "1.0"
type: code
""",
    )

    with pytest.raises(ValueError, match="Invalid plugin metadata"):
        PluginRegistry(str(tmp_path)).load_plugins()


def test_container_without_image_is_rejected(tmp_path):
    write_plugin(
        tmp_path,
        """
name: sample
version: "1.0"
type: container
provides:
  - database
""",
    )

    with pytest.raises(ValueError, match="must define an image"):
        PluginRegistry(str(tmp_path)).load_plugins()


def test_unknown_metadata_field_is_rejected(tmp_path):
    write_plugin(
        tmp_path,
        """
name: sample
version: "1.0"
type: code
runtime_dependecies:
  - redis
""",
    )

    with pytest.raises(ValueError, match="runtime_dependecies"):
        PluginRegistry(str(tmp_path)).load_plugins()


def test_malformed_yaml_is_rejected(tmp_path):
    write_plugin(
        tmp_path,
        """
name: [sample
version: "1.0"
type: code
""",
    )

    with pytest.raises(ValueError, match="Invalid plugin metadata"):
        PluginRegistry(str(tmp_path)).load_plugins()


def test_plugin_name_must_match_directory_name(tmp_path):
    write_plugin(
        tmp_path,
        """
name: different_name
version: "1.0"
type: code
""",
    )

    with pytest.raises(ValueError, match="must match its directory name"):
        PluginRegistry(str(tmp_path)).load_plugins()
