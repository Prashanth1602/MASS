import yaml
import pytest

from app.plugin_scaffolder import PluginScaffolder


def test_create_plugin_generates_expected_files(tmp_path):
    scaffolder = PluginScaffolder(tmp_path / "plugins")

    plugin_directory = scaffolder.create("greeting")

    assert (plugin_directory / "plugin.yaml").is_file()
    assert (plugin_directory / "templates" / "router.py").is_file()
    assert (plugin_directory / "templates" / "service.py").is_file()

    manifest = yaml.safe_load(
        (plugin_directory / "plugin.yaml").read_text()
    )

    assert manifest["name"] == "greeting"
    assert manifest["type"] == "code"
    assert manifest["provides"] == ["greeting"]


@pytest.mark.parametrize(
    "name",
    ["", "Greeting", "123plugin", "../outside", "plugin name"],
)
def test_create_plugin_rejects_invalid_names(tmp_path, name):
    scaffolder = PluginScaffolder(tmp_path / "plugins")

    with pytest.raises(ValueError):
        scaffolder.create(name)


def test_create_plugin_does_not_overwrite_existing_directory(tmp_path):
    plugins_directory = tmp_path / "plugins"
    existing_directory = plugins_directory / "greeting"
    existing_directory.mkdir(parents=True)

    marker = existing_directory / "keep.txt"
    marker.write_text("preserve this")

    scaffolder = PluginScaffolder(plugins_directory)

    with pytest.raises(FileExistsError):
        scaffolder.create("greeting")

    assert marker.read_text() == "preserve this"
