from typing import Any

from pydantic import BaseModel


class ApplicationConfig(BaseModel):
    name: str


class BuildRequest(BaseModel):
    application: ApplicationConfig
    plugins: dict[str, dict[str, Any]]