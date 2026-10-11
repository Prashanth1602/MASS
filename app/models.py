from typing import Any

from pydantic import BaseModel, Field

class ApplicationConfig(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    host_port: int = Field(default=8000, ge=1, le=65535)


class BuildRequest(BaseModel):
    application: ApplicationConfig
    plugins: dict[str, dict[str, Any]]