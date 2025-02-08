from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.utils import get_current_user
from src.models.models import User
from src.auth.repos import UserRepository
from src.subscription.repos import SubscriptionRepository


router = APIRouter()


# Підписатися
@router.post("/subscribe/{user_id}", status_code=status.HTTP_200_OK)
async def subscribe(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe to a user.

    This route allows the current user to subscribe to another user if:
    - Both users are active.
    - The user is not trying to subscribe to themselves.
    - The user is not already subscribed to the target user.

    Args:
        user_id (int): The ID of the user to subscribe to.
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user is not active, the target user is not found,
                        the user is trying to subscribe to themselves, or is already subscribed.

    Returns:
        Response: Successful subscription creation.
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
    sub_repo = SubscriptionRepository(db)
    if await sub_repo.check_existing_subscription(current_user.id, user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already subscribed.",
        )
    return await sub_repo.create_subscription(current_user.id, user.id)


# Відписатися
@router.delete("/unsubscribe/{user_id}", status_code=status.HTTP_200_OK)
async def unsubscribe(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unsubscribe from a user.

    This route allows the current user to unsubscribe from another user if:
    - Both users are active.
    - The user is not trying to unsubscribe from themselves.
    - The user is already subscribed to the target user.

    Args:
        user_id (int): The ID of the user to unsubscribe from.
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user is not active, the target user is not found,
                        the user is trying to unsubscribe from themselves, or is not subscribed.

    Returns:
        Response: Successful subscription deletion.
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
            detail="You can't unsubscribe yourself.",
        )
    sub_repo = SubscriptionRepository(db)
    if not await sub_repo.check_existing_subscription(current_user.id, user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not subscribed.",
        )
    return await sub_repo.delete_subscription(current_user.id, user.id)


# Переглянути всі підписки (тих на кого підписаний юзер)
@router.get("/subscriptions", status_code=status.HTTP_200_OK)
async def get_all_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    View all subscriptions of the current user (users the current user is subscribed to).

    This route returns a list of users to whom the current user is subscribed.

    Args:
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user is not active or has no subscriptions.

    Returns:
        dict: A list of the current user's subscriptions.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    sub_repo = SubscriptionRepository(db)
    subscriptions = await sub_repo.get_all_subscriptions(current_user.id)
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No subscriptions found"
        )
    return {"my subscriptions": [user.username for user in subscriptions]}


# Переглянути всіx підписників (тих хто підписаний на юзера)
@router.get("/subscribers", status_code=status.HTTP_200_OK)
async def get_all_subscribers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    View all subscribers of the current user (users who are subscribed to the current user).

    This route returns a list of users who are subscribed to the current user.

    Args:
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user is not active or has no subscribers.

    Returns:
        dict: A list of the current user's subscribers.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )
    sub_repo = SubscriptionRepository(db)
    subscribers = await sub_repo.get_all_subscribers(current_user.id)
    if not subscribers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No subscribers found"
        )
    return {"my subscribers": [user.username for user in subscribers]}


# Перевірка чи підписаний інший юзер на поточного юзера
@router.get("/is_subscribed/{username}", status_code=status.HTTP_200_OK)
async def is_subscribed(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if another user is subscribed to the current user.

    This route allows checking if a user with the given username is subscribed to the current user.

    Args:
        username (str): The username of the user to check subscription status.
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user is not found or not active.

    Returns:
        dict: Subscription status.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(username)
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
            detail="You can't check subscription status for yourself.",
        )
    sub_repo = SubscriptionRepository(db)
    is_subscribed = await sub_repo.check_is_subscribed(user.id, current_user.id)
    return {"is_subscribed": is_subscribed}


# Перевірка чи підписаний поточний юзер на іншого юзера
@router.get("/is_subscribed_by/{username}", status_code=status.HTTP_200_OK)
async def is_subscribed_by(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if the current user is subscribed to another user.

    This route allows checking if the current user is subscribed to a user with the given username.

    Args:
        username (str): The username of the user to check subscription status.
        db (AsyncSession): Database session.
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user is not found or not active.

    Returns:
        dict: Subscription status.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(username)
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
            detail="You can't check subscription status for yourself.",
        )
    sub_repo = SubscriptionRepository(db)
    is_subscribed = await sub_repo.check_is_subscribed_by(user.id, current_user.id)
    return {"is_subscribed": is_subscribed}
