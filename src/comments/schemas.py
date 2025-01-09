from datetime import datetime

from pydantic import BaseModel


class Comment(BaseModel):
    photo_id: int
    content: str


class CommentCreate(BaseModel):
    photo_id: int
    content: str


class CommentResponse(BaseModel):
    id: int
    user_id: int
    photo_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
