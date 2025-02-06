from datetime import datetime

from pydantic import BaseModel


class Reaction(BaseModel):
    id: int
    name: str

class ReactionResponse(BaseModel):
    reaction_id: int
    name: str
    user_id: int
    photo_id: int
    created_at: datetime

class ReactionRequest(BaseModel):
    reaction_id: int
    photo_id: int

