from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.models import Message, User


class MessageRepository:

    def __init__(self, session: AsyncSession):
        self.session = session
