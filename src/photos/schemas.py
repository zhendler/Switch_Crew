from pydantic import BaseModel
from typing import List, Optional


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int

    class Config:
        orm_mode = True


class PhotoBase(BaseModel):
    url: str
    tags: Optional[List[TagCreate]] = []
    description: Optional[str] = None


class PhotoCreate(PhotoBase):
    pass


class PhotoResponse(PhotoBase):
    id: int
    url: str
    qr_code_url: Optional[str]
    tags: List[TagResponse] = []

    class Config:
        orm_mode = True
