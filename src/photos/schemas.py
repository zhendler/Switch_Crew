from pydantic import BaseModel
from typing import List, Optional


class PhotoBase(BaseModel):
    url: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class PhotoCreate(PhotoBase):
    pass


class PhotoResponse(PhotoBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class PhotoUpdate(BaseModel):
    description: str