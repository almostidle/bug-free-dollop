from pydantic import BaseModel


class ConfigOut(BaseModel):
    key: str
    value: str
    description: str | None = None

    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    value: str
