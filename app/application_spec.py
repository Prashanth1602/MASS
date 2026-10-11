from pathlib import Path
import re
import os
from typing import Any


import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def resolve_environment_variables(value):
    if isinstance(value, dict):
        return {
            key: resolve_environment_variables(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            resolve_environment_variables(item)
            for item in value
        ]

    if not isinstance(value, str):
        return value

    def replace(match):
        variable_name = match.group(1)
        environment_value = os.environ.get(variable_name)

        if environment_value is None:
            raise ValueError(
                f"Environment variable '{variable_name}' is not set"
            )

        return environment_value

    return ENV_VAR_PATTERN.sub(replace, value)



class ApplicationSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    host_port: int = Field(default=8000, ge=1, le=65535)
    plugins: dict[str, dict[str, Any]]


def load_application_spec(path: str | Path) -> ApplicationSpecification:
    spec_path = Path(path)

    try:
        with spec_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except OSError as exc:
        raise ValueError(
            f"Cannot read application specification '{spec_path}': {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in '{spec_path}': {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Application specification must be a YAML mapping")

    try:
        resolved_data = resolve_environment_variables(data)
        return ApplicationSpecification.model_validate(resolved_data)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid application specification: {exc}"
        ) from exc
