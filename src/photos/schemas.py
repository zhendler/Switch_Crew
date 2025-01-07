
from fastapi import Query
from pydantic import BaseModel, Field
from typing import List, Optional


class PhotoBase(BaseModel):
    id: int
    url_link: str



class PhotoCreate(BaseModel):
    description: Optional[str] = Field(None, max_length=255, description= "Description of the photo")
    tags: List[str] = Query([], title="Теги")

class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PhotoResponse(PhotoBase):

    id: int
    owner_id: int
    description: Optional[str] = None
    tags: List[TagResponse]
    rating: Optional[float]
    qr_core_url: Optional[str]

    class Config:
        from_attributes = True


class PhotoUpdate(BaseModel):
    description: str


class UrlPhotoResponse(BaseModel):
    url_link: str


class GetPhoto(BaseModel):
    photo_id: int

class PhotoRatingResponse(BaseModel):
    user_id: int
    rating: int

    class Config:
        from_attributes = True

# Схема для списку всіх оцінок фото
class PhotoRatingsListResponse(BaseModel):
    photo_id: int
    ratings: List[PhotoRatingResponse]

    class Config:
        from_attributes = True

# Схема для списку всіх оцінок користувача
class UserRatingsListResponse(BaseModel):
    user_id: int
    ratings: List[PhotoRatingResponse]

    class Config:
        from_attributes = True



class AverageRatingResponse(BaseModel):
    rating: float

    class Config:
        from_attributes = True