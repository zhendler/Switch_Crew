from pydantic import BaseModel
from typing import List, Optional


class PhotoBase(BaseModel):
    url: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class PhotoCreate(PhotoBase):
    pass


class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PhotoResponse(PhotoBase):
    id: int
    user_id: int
    description: Optional[str] = None
    tags: List[TagResponse]

    class Config:
        from_attributes = True


class PhotoUpdate(BaseModel):
    description: str

class TransformRequest(BaseModel):
    photo_id: int
    width: int
    height: int
    crop_mode: str = "fill"

class TransformResponse(BaseModel):
    photo_id: int
    transformed_url: str
    qr_code_url: str