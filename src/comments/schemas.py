from datetime import datetime
from fastapi.params import Query
from pydantic import BaseModel



class Comment(BaseModel):
    photo_id: int
    content: str


class CommentCreate(BaseModel):
        content: str = Query(..., min_length=1, max_length=255, description="Текст коментаря")

class CommentResponse(BaseModel):
    id: int
    user_id: int
    photo_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentUpdateResponse(BaseModel):
    id: int
    user_id: int
    photo_id: int
    content: str
    updated_at: datetime