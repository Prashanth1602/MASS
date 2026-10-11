import argparse
import sys

from fastapi import HTTPException

from app.application_service import ApplicationService
from app.application_spec import load_application_spec
from app.models import ApplicationConfig, BuildRequest
from app.plugin_registry import PluginRegistry
from app.main import build_application as build_application_request
from app.runtime_manager import run_application, stop_application


def validate_application(spec_path: str) -> int:
    try:
        specification = load_application_spec(spec_path)

        registry = PluginRegistry()
        registry.load_plugins()

        service = ApplicationService(registry)

        request = BuildRequest(
            application=ApplicationConfig(name=specification.name, host_port=specification.host_port),
            plugins=specification.plugins,
        )

        selected_plugins, dependencies = service.prepare(request)

    except (ValueError, OSError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Application '{specification.name}' is valid.")
    print(f"Selected plugins: {', '.join(p['name'] for p in selected_plugins)}")
    print(f"Dependencies: {dependencies}")
    print("No application files were generated.")

    return 0


def build_application_from_spec(spec_path: str) -> int:
    try:
        specification = load_application_spec(spec_path)

        request = BuildRequest(
            application=ApplicationConfig(name=specification.name, host_port=specification.host_port),
            plugins=specification.plugins,
        )

        result = build_application_request(request)

    except HTTPException as exc:
        print(f"Build failed: {exc.detail}", file=sys.stderr)
        return 1

    except (ValueError, OSError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1

    print(result["message"])
    print(f"Application: {result['application']}")
    print(f"Plugins: {', '.join(result['plugins'])}")
    print(f"Compose file: {result['compose_file']}")

    return 0

def list_plugins() -> int:
    registry = PluginRegistry()

    try:
        registry.load_plugins()
    except (ValueError, OSError) as exc:
        print(f"Error loading plugins: {exc}", file=sys.stderr)
        return 1

    plugins = registry.list_plugins()

    if not plugins:
        print("No plugins found.")
        return 0

    print(f"\nMASS — Available Plugins ({len(plugins)})\n")

    name_width = max(
        len("NAME"),
        max(len(plugin["name"]) for plugin in plugins),
    )

    version_width = max(
        len("VERSION"),
        max(len(plugin["version"]) for plugin in plugins),
    )

    header = (
        f"{'NAME':<{name_width}}  "
        f"{'VERSION':<{version_width}}  "
        f"{'TYPE':<10}  CAPABILITIES"
    )

    print(header)
    print("-" * len(header))

    for plugin in plugins:
        capabilities = ", ".join(plugin.get("provides", [])) or "-"

        print(
            f"{plugin['name']:<{name_width}}  "
            f"{plugin['version']:<{version_width}}  "
            f"{plugin['type']:<10}  "
            f"{capabilities}"
        )

    print()
    return 0


def inspect_plugin(plugin_name: str) -> int:
    registry = PluginRegistry()

    try:
        registry.load_plugins()
    except (ValueError, OSError) as exc:
        print(f"Error loading plugins: {exc}", file=sys.stderr)
        return 1

    plugin = registry.get(plugin_name)

    if plugin is None:
        print(f"Plugin '{plugin_name}' not found.", file=sys.stderr)
        return 1

    print(f"\nPlugin: {plugin['name']}")
    print(f"Version: {plugin['version']}")
    print(f"Type: {plugin['type']}")

    if plugin.get("image"):
        image = plugin["image"]
        print(f"Image: {image['repository']}:{image['tag']}")

    print("\nProvides:")
    for capability in plugin.get("provides", []):
        print(f"  - {capability}")

    print("\nRequires:")
    for capability in plugin.get("requires", []):
        print(f"  - {capability}")

    print("\nConfiguration:")
    for name, definition in plugin.get("configuration", {}).items():
        details = [definition["type"]]

        details.append(
            "required" if definition.get("required") else "optional"
        )

        if definition.get("secret"):
            details.append("secret")

        if "default" in definition and not definition.get("secret"):
            details.append(f"default={definition['default']}")

        print(f"  {name}: {', '.join(details)}")

    print("\nInputs:")
    for name, definition in plugin.get("inputs", {}).items():
        print(f"  {name}: {definition['from']} ({definition['type']})")

    print("\nOutputs:")
    for name, definition in plugin.get("outputs", {}).items():
        details = [definition["type"]]

        if definition.get("secret"):
            details.append("secret")

        print(f"  {name}: {', '.join(details)}")

    print()
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mass",
        description="MASS — Modular App Service Stack",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # Plugin commands
    plugins_parser = subparsers.add_parser(
        "plugins",
        help="Manage and inspect plugins",
    )

    plugins_subparsers = plugins_parser.add_subparsers(
        dest="plugins_command",
        required=True,
    )

    plugins_subparsers.add_parser(
        "list",
        help="List available plugins",
    )

    inspect_parser = plugins_subparsers.add_parser(
        "inspect",
        help="Inspect a plugin's metadata",
    )
    inspect_parser.add_argument("name", help="Plugin name")

    # Application commands
    app_parser = subparsers.add_parser(
        "app",
        help="Validate and build applications",
    )

    app_subparsers = app_parser.add_subparsers(
        dest="app_command",
        required=True,
    )

    validate_parser = app_subparsers.add_parser(
        "validate",
        help="Validate an application specification",
    )
    validate_parser.add_argument(
        "spec",
        help="Path to YAML specification",
    )

    build_parser = app_subparsers.add_parser(
        "build",
        help="Generate an application from a specification",
    )
    build_parser.add_argument(
        "spec",
        help="Path to YAML specification",
    )

    run_parser = app_subparsers.add_parser(
        "run",
        help="Build and start a generated application",
    )
    run_parser.add_argument("name", help="Generated application name")

    stop_parser = app_subparsers.add_parser(
        "stop",
        help="Stop a generated application",
    )
    stop_parser.add_argument("name", help="Generated application name")

    args = parser.parse_args()

    # Dispatch commands
    if args.command == "plugins":
        if args.plugins_command == "list":
            return list_plugins()

        if args.plugins_command == "inspect":
            return inspect_plugin(args.name)

    if args.command == "app":
        if args.app_command == "validate":
            return validate_application(args.spec)

        if args.app_command == "build":
            return build_application_from_spec(args.spec)

        if args.app_command == "run":
            return run_application(args.name)

        if args.app_command == "stop":
            return stop_application(args.name)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
