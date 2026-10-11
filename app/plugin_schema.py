from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImageDefinition(StrictModel):
    repository: str = Field(min_length=1)
    tag: str = Field(min_length=1)


class ConfigurationField(StrictModel):
    type: Literal["string", "integer", "number", "boolean"]
    required: bool = False
    default: Any = None
    secret: bool = False


class InputDefinition(StrictModel):
    from_: str = Field(alias="from", min_length=1)


class OutputDefinition(StrictModel):
    value: Any
    secret: bool = False


class VolumeDefinition(StrictModel):
    name: str = Field(min_length=1)
    target: str = Field(min_length=1)


class PluginDefinition(StrictModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    version: str = Field(min_length=1)
    type: Literal["container", "code"]

    image: ImageDefinition | None = None

    provides: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)

    configuration: dict[str, ConfigurationField] = Field(
        default_factory=dict
    )
    inputs: dict[str, InputDefinition] = Field(default_factory=dict)
    outputs: dict[str, OutputDefinition] = Field(default_factory=dict)

    environment: dict[str, str] = Field(default_factory=dict)
    volumes: list[VolumeDefinition] = Field(default_factory=list)
    runtime_dependencies: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_plugin_type(self):
        if self.type == "container" and self.image is None:
            raise ValueError(
                "Container plugins must define an image with "
                "'repository' and 'tag'"
            )

        if self.type == "code" and self.volumes:
            raise ValueError(
                "Code plugins cannot declare container volumes"
            )

        return self
