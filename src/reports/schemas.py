from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ReportStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReportBase(BaseModel):
    id: int
    user_id: int
    reported_user_id: int
    reason: str
    created_at: datetime  # Час створення скарги

class ReportPhotoCreate(ReportBase):
    user_id: int                      # Користувач, що подає скаргу
    reason: str                       # Причина скарги
    photo_id: int                     # ID фото, на яке скаржаться
    reported_user_id: int             # ID користувача, власника фото

class ReportCommentCreate(BaseModel):
    user_id: int
    reason: str
    comment_id: int
    reported_user_id: int

    class Config:
        from_attributes = True

class ReportPhotoResponse(ReportBase):
    photo_id: int            # ID фото, на яке скаржаться

    class Config:
        from_attributes = True

class ReportCommentResponse(ReportBase):
    comment_id: int          # ID коментаря, на який скаржаться

    class Config:
        from_attributes = True
