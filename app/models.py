from typing import Any

from pydantic import BaseModel, Field

class ApplicationConfig(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")


class BuildRequest(BaseModel):
    application: ApplicationConfig
    plugins: dict[str, dict[str, Any]]