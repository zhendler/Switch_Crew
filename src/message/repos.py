from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_

from src.models.models import User, Message
from src.message.schemas import (
    MessageCreate,
    SentMessageResponse,
    ReceivedMessageResponse,
)


class MessageRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_message(
        self, sender_id: int, receiver_id: int, message_model: MessageCreate
    ) -> Message:
        query = select(User).filter(User.id == receiver_id)
        result = await self.session.execute(query)
        receiver = result.scalars().first()
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found"
            )
        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=message_model.content,
        )
        new_message.receiver_username = receiver.username
        self.session.add(new_message)
        await self.session.commit()
        await self.session.refresh(new_message)
        return new_message

    async def get_message_by_id(self, message_id: int) -> Message | None:
        result = await self.session.execute(
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.sender))
        )
        return result.scalars().first()

    async def get_sent_messages(
        self, sender_id: int, receiver_id: int | None = None, limit: int = 30
    ) -> list[SentMessageResponse]:
        if receiver_id:
            result = await self.session.execute(
                select(User).where(User.id == receiver_id)
            )
            receiver = result.scalars().first()
            if not receiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Receiver with ID {receiver_id} not found",
                )
        stmt = (
            select(Message)
            .where(Message.sender_id == sender_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .options(selectinload(Message.resiver))
        )
        if receiver_id:
            stmt = stmt.where(Message.receiver_id == receiver_id)
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sent messages found.",
            )
        message_response = []
        for message in messages:
            receiver_username = message.resiver.username if message.resiver else None
            message_response.append(
                {
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "receiver_username": receiver_username,
                    "content": message.content,
                    "created_at": message.created_at,
                }
            )
        return message_response

    async def get_received_messages(
        self, receiver_id: int, sender_id: int | None = None, limit: int = 30
    ) -> list[ReceivedMessageResponse]:
        if sender_id:
            result = await self.session.execute(
                select(User).where(User.id == sender_id)
            )
            sender = result.scalars().first()
            if not sender:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sender with ID {sender_id} not found",
                )
        stmt = (
            select(Message)
            .where(Message.receiver_id == receiver_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .options(selectinload(Message.sender))
        )
        if sender_id:
            stmt = stmt.where(Message.sender_id == sender_id)
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No received messages found.",
            )
        message_response = []
        for message in messages:
            sender_username = message.sender.username if message.sender else None
            message_response.append(
                {
                    "id": message.id,
                    "receiver_id": message.receiver_id,
                    "sender_id": message.sender_id,
                    "sender_username": sender_username,
                    "content": message.content,
                    "created_at": message.created_at,
                }
            )
        return message_response

    async def get_unread_messages(
        self, receiver_id: int, sender_id: int | None = None, limit: int = 30
    ) -> list[Message]:
        if sender_id:
            result = await self.session.execute(
                select(User).where(User.id == sender_id)
            )
            sender = result.scalars().first()
            if not sender:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sender with ID {sender_id} not found",
                )
        stmt = (
            select(Message)
            .where(and_(Message.receiver_id == receiver_id, Message.is_read.is_(False)))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        if sender_id:
            stmt = stmt.where(Message.sender_id == sender_id)
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        unread_message_response = []
        for message in messages:
            sender_username = message.sender.username if message.sender else None
            unread_message_response.append(
                {
                    "id": message.id,
                    "receiver_id": message.receiver_id,
                    "sender_id": message.sender_id,
                    "sender_username": sender_username,
                    "content": message.content,
                    "created_at": message.created_at,
                }
            )
        return unread_message_response

    async def mark_as_read(self, message: Message) -> None:
        message.is_read = True
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

    async def delete_message(self, message_id: int) -> None:
        stmt = select(Message).where(Message.id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalars().one_or_none()
        if message:
            await self.session.delete(message)
            await self.session.commit()

    async def update_message_content(
        self, message_id: int, new_content: str
    ) -> Message | None:
        stmt = select(Message).where(Message.id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalars().one_or_none()
        if message:
            message.content = new_content
            message.updated_at = datetime.now()
            self.session.add(message)
            await self.session.commit()
            await self.session.refresh(message)
        return message

    async def get_chat_history(self, user_id: int, limit: int = 30) -> list[Message]:
        if user_id:
            result = await self.session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found",
                )
        stmt = (
            select(Message)
            .where((Message.sender_id == user_id) | (Message.receiver_id == user_id))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .options(selectinload(Message.sender), selectinload(Message.resiver))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
