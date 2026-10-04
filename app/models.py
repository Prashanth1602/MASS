from pydantic import BaseModel


class ApplicationConfig(BaseModel):
    name: str


class BuildRequest(BaseModel):
    application: ApplicationConfig
    plugins: list[str] 