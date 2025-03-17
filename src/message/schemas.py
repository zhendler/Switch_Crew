from datetime import datetime
from pydantic import BaseModel
from typing import List


class MessageSchema(BaseModel):
    id: int
    sender_id: int
    resiver_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
