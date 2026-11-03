from pydantic import BaseModel, ConfigDict


class ConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str
    description: str | None = None


class ConfigUpdate(BaseModel):
    value: str
