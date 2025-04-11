from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str


class SentMessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    receiver_username: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReceivedMessageResponse(BaseModel):
    id: int
    receiver_id: int
    sender_id: int
    sender_username: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageUpdateResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
