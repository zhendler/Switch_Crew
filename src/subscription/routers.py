from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.utils import get_current_user
from src.models.models import Subscription
from src.models.models import User
from src.auth.repos import UserRepository


router = APIRouter()


@router.post("/subscribe/{user_id}", status_code=status.HTTP_200_OK)
async def subscribe(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe to a user's posts.

    Args:
        user_id (int): The user to subscribe to.
        db (AsyncSession): The database session.
        current_user (User): The currently authenticated user.

    Returns:
        None
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(user_id)
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't subscribe to yourself.",
        )
    query = select(Subscription).where(
        Subscription.subscriber_id == current_user.id,
        Subscription.subscribed_to_id == user.id,
    )
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already subscribed.",
        )
    subscription = Subscription(subscriber_id=current_user.id, subscribed_to_id=user.id)
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return {"message": "Subscription completed"}


@router.delete("/subscribe/{user_id}", status_code=status.HTTP_200_OK)
async def subscribe(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unsubscribe from a user's posts.

    Args:
        user_id (int): The user to unsubscribe from.
        db (AsyncSession): The database session.
        current_user (User): The currently authenticated user.

    Returns:
        dict: A message confirming the cancellation of the subscription.

    Raises:
        HTTPException: If the user is not subscribed to the given user.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(user_id)
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    query = select(Subscription).where(
        Subscription.subscriber_id == current_user.id,
        Subscription.subscribed_to_id == user.id,
    )
    result = await db.execute(query)
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You are not subscribed."
        )
    await db.delete(subscription)
    await db.commit()
    return {"message": "Subscription canceled."}
