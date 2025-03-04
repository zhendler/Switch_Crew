from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.auth.schemas import UserBase


class Comment(BaseModel):
    photo_id: int
    content: str


class CommentCreate(BaseModel):
    photo_id: int
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    photo_id: Optional[int] = None
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserBase
    replies: Optional[list["CommentResponse"]]

    class Config:
        from_attributes = True

class CommentResponseComment(BaseModel):
    id: int
    user_id: int
    parent_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True