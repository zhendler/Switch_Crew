from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, Message
from config.db import get_db
from src.auth.utils import get_current_user
from src.message.repos import MessageRepository
from src.message.schemas import (
    MessageCreate,
    SentMessageResponse,
    ReceivedMessageResponse,
    MessageUpdateResponse,
    ChatHistoryResponse,
)


router = APIRouter()


@router.post(
    "/send-message",
    response_model=SentMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    receiver_id: int,
    message_model: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    if receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a message to yourself.",
        )
    message_repo = MessageRepository(db)
    message = await message_repo.create_message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message_model=message_model,
    )
    return message


@router.get(
    "/sent-messages",
    response_model=list[SentMessageResponse],
    status_code=status.HTTP_200_OK,
)
async def get_last_sent_messages(
    receiver_id: int = Query(None, description="Receiver ID (Optional)"),
    limit: int = Query(30, ge=1, le=30, description="Maximum number of messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    if receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot send a message to yourself.",
        )
    message_repo = MessageRepository(db)
    messages = await message_repo.get_sent_messages(
        sender_id=current_user.id, receiver_id=receiver_id, limit=limit
    )
    return messages


@router.get(
    "/received-messages",
    response_model=list[ReceivedMessageResponse],
    status_code=status.HTTP_200_OK,
)
async def get_last_received_messages(
    sender_id: int = Query(None, description="Sender ID (Optional)"),
    limit: int = Query(30, ge=1, le=30, description="Maximum number of messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    if sender_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot be the receiver of a message from yourself.",
        )
    message_repo = MessageRepository(db)
    messages = await message_repo.get_received_messages(
        receiver_id=current_user.id, sender_id=sender_id, limit=limit
    )
    return messages


@router.get(
    "/unread-messages",
    response_model=list[ReceivedMessageResponse],
    status_code=status.HTTP_200_OK,
)
async def get_last_unread_messages(
    sender_id: int = Query(None, description="Sender ID (Optional)"),
    limit: int = Query(30, ge=1, le=30, description="Maximum number of messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    if sender_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot be the receiver of a message from yourself.",
        )
    message_repo = MessageRepository(db)
    unread_messages = await message_repo.get_unread_messages(
        receiver_id=current_user.id, sender_id=sender_id, limit=limit
    )
    if not unread_messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No unread messages found.",
        )
    for message_dict in unread_messages:
        message = await db.get(Message, message_dict["id"])
        await message_repo.mark_as_read(message)
    return unread_messages


@router.get(
    "/chat-history/{user_id}",
    response_model=list[ChatHistoryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_chat_history_by_user_id(
    user_id: int,
    limit: int = Query(30, ge=1, le=30, description="Maximum number of messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    message_repo = MessageRepository(db)
    messages = await message_repo.get_chat_history(user_id=user_id, limit=limit)
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No messages found.",
        )
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot get chat history with yourself.",
        )
    return messages


@router.delete("/delete-message/{message_id}", status_code=status.HTTP_200_OK)
async def delete_own_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    message_repo = MessageRepository(db)
    message = await message_repo.get_message_by_id(message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found."
        )
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own messages.",
        )
    await message_repo.delete_message(message_id)
    return {"detail": "Message deleted successfully."}


@router.put(
    "/update-message/{message_id}",
    response_model=MessageUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_own_message(
    message_id: int,
    message_model: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    message_repo = MessageRepository(db)
    message = await message_repo.get_message_by_id(message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found."
        )
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can update only your own messages.",
        )
    updated_message = await message_repo.update_message_content(
        message_id, message_model.content
    )
    return updated_message
