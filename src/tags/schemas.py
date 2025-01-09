from pydantic import BaseModel


class TagBase(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TagResponse(TagBase):
    pass
