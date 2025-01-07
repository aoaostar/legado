from pydantic import BaseModel, Field


class BaseSource(BaseModel):
    title: str
    url: str
    home_page: str = ""
    tags: list[str] = Field(default_factory=list)
