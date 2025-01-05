from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    country: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[datetime] = None 
    country: Optional[str] = None
    created_at: datetime
    uploaded_photos: int

    class Config:
        from_attributes = True

class AdminUserProfileResponse(UserProfileResponse):
    role_name: str
    is_active: bool
    is_banned: bool

class UserAvatarResponse(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True