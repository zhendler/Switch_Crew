from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_

from src.models.models import User, Message
from src.message.error_handlers import check_exists
from src.message.schemas import (
    MessageCreate,
    SentMessageResponse,
    ReceivedMessageResponse,
)


class MessageRepository:
    """Repository class for handling database operations related to messages.
    Provides methods for creating, retrieving, updating, and deleting messages,
    as well as managing message status (read/unread) and retrieving chat history.
    Args:
        session: An asynchronous SQLAlchemy session for database operations.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the MessageRepository with a database session.
        Args:
            session: An asynchronous SQLAlchemy session for database operations.
        """
        self.session = session

    async def create_message(
        self, sender_id: int, receiver_id: int, message_model: MessageCreate
    ) -> Message:
        """Create and store a new message in the database.
        Args:
            sender_id: ID of the user sending the message.
            receiver_id: ID of the intended message recipient.
            message_model: Pydantic model containing message content.
        Returns:
            The newly created Message object.
        Raises:
            HTTPException: 404 Not Found if the receiver doesn't exist.
        """
        query = select(User).filter(User.id == receiver_id)
        result = await self.session.execute(query)
        receiver = result.scalars().first()
        check_exists(receiver, "Receiver not found.")
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
        """Retrieve a single message by its ID.
        Args:
            message_id: The ID of the message to retrieve.
        Returns:
            The Message object if found, None otherwise.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.sender))
        )
        return result.scalars().first()

    async def get_sent_messages(
        self, sender_id: int, receiver_id: int | None = None, limit: int = 30
    ) -> list[SentMessageResponse]:
        """Retrieve messages sent by a specific user.
        Args:
            sender_id: ID of the user who sent the messages.
            receiver_id: Optional ID to filter messages by specific recipient.
            limit: Maximum number of messages to return (default: 30).
        Returns:
            List of sent messages with receiver information.
        Raises:
            HTTPException: 404 Not Found if no messages are found.
        """
        receiver = None
        if receiver_id:
            query = select(User).filter(User.id == receiver_id)
            result = await self.session.execute(query)
            receiver = result.scalars().first()
            check_exists(receiver, "Receiver not found.")
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
        check_exists(messages, "No sent messages found.")
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
        """Retrieve messages received by a specific user.
        Args:
            receiver_id: ID of the user who received the messages.
            sender_id: Optional ID to filter messages by specific sender.
            limit: Maximum number of messages to return (default: 30).
        Returns:
            List of received messages with sender information.
        Raises:
            HTTPException: 404 Not Found if no messages are found.
        """
        sender = None
        if sender_id:
            query = select(User).filter(User.id == sender_id)
            result = await self.session.execute(query)
            sender = result.scalars().first()
            check_exists(sender, "Sender not found.")
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
        check_exists(messages, "No received messages found.")
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
        """Retrieve unread messages for a specific user.
        Args:
            receiver_id: ID of the user who received the messages.
            sender_id: Optional ID to filter messages by specific sender.
            limit: Maximum number of messages to return (default: 30).
        Returns:
            List of unread messages with sender information.
        """
        sender = None
        if sender_id:
            query = select(User).filter(User.id == sender_id)
            result = await self.session.execute(query)
            sender = result.scalars().first()
            check_exists(sender, "Sender not found.")
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
        """Mark a message as read.
        Args:
            message: The Message object to mark as read.
        """
        message.is_read = True
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

    async def delete_message(self, message_id: int) -> None:
        """Delete a message from the database.
        Args:
            message_id: ID of the message to delete.
        """
        stmt = select(Message).where(Message.id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalars().one_or_none()
        if message:
            await self.session.delete(message)
            await self.session.commit()

    async def update_message_content(
        self, message_id: int, new_content: str
    ) -> Message | None:
        """Update the content of an existing message.
        Args:
            message_id: ID of the message to update.
            new_content: New content for the message.
        Returns:
            The updated Message object if found, None otherwise.
        """
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

    async def get_chat_history(
        self,
        user_id: int,
        current_user_id: int,
        limit: int = 30,
    ) -> list[Message]:
        """Retrieve chat history between two users.
        Args:
            user_id: ID of the other participant in the conversation.
            current_user_id: ID of the current authenticated user.
            limit: Maximum number of messages to return (default: 30).
        Returns:
            List of messages exchanged between the two users, ordered by creation time.
        Raises:
            HTTPException: 404 Not Found if the other user doesn't exist.
        """
        if user_id:
            result = await self.session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            check_exists(user, "User not found.")
        stmt = (
            select(Message)
            .where(
                (
                    (Message.sender_id == current_user_id)
                    & (Message.receiver_id == user_id)
                )
                | (
                    (Message.sender_id == user_id)
                    & (Message.receiver_id == current_user_id)
                )
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
            .options(selectinload(Message.sender), selectinload(Message.resiver))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
