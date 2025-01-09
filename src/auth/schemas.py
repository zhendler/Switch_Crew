from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class RoleEnum(Enum):
    ADMIN = "Admin"
    MODERATOR = "Moderator"
    USER = "User"


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    detail: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
