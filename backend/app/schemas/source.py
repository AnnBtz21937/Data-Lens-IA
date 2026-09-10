from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    type: str
    path: str | None = None