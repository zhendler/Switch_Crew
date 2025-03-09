from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ReportStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReportBase(BaseModel):
    reason: str

class ReportCreate(ReportBase):
    photo_id: Optional[int] = None
    comment_id: Optional[int] = None
    reported_user_id: Optional[int] = None

class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: datetime

    class Config:
        from_attributes = True
