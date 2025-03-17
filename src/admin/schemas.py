from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from enum import Enum


class UserForAdmin(BaseModel):
    id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    birth_date: Optional[date]
    country: Optional[str]
    is_banned: bool
    email: str
    is_active: bool
    role_id: Optional[int]
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserFullInformationAdmin(UserForAdmin):
    photos_count: int
    comments_count: int

class UserNameForAdmin(BaseModel):
    username: str

    class Config:
        from_attributes = True

class PhotoForComments(BaseModel):
    url_link: str

class UserCommentsForAdmin(BaseModel):
    id: int
    content: str
    user_id: int
    photo_id: int
    created_at: datetime
    updated_at: datetime
    photo: PhotoForComments

    class Config:
        from_attributes = True

class RoleEnum(Enum):
    ADMIN = "Admin"
    MODERATOR = "Moderator"
    USER = "User"


