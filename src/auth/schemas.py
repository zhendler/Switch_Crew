from enum import Enum
from pydantic import BaseModel, EmailStr


class RoleEnum(Enum):
    ADMIN = "Admin"
    MODERATOR = "Moderator"
    USER = "User"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    

class UserCreate(UserBase):
    username: str
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_atributes = True


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str