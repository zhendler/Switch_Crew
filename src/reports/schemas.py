from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ReportStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReportCreateBase(BaseModel):
    reason: str


class ReportPhotoCreate(ReportCreateBase):
    photo_id: int                     # ID фото, на яке скаржаться

    class Config:
        from_attributes = True

class ReportCommentCreate(ReportCreateBase):
    comment_id: int

    class Config:
        from_attributes = True

class ReportPhotoResponse(BaseModel):
    id: int
    user_id: int
    reported_user_id: int
    photo_id: int
    reason: str
    status: ReportStatus
    created_at: datetime

    class Config:
        from_attributes = True

class ReportCommentResponse(ReportCreateBase):
    comment_id: int          # ID коментаря, на який скаржаться

    class Config:
        from_attributes = True
