from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


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