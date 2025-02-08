from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Subscription
from src.models.models import User


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_existing_subscription(
        self, subscriber_id: int, subscribed_to_id: int
    ) -> bool:
        """
        Check if a subscription already exists between two users.

        This method checks if a subscription exists between a subscriber and a user they are subscribed to.

        Args:
            subscriber_id (int): The ID of the user who is subscribing.
            subscribed_to_id (int): The ID of the user being subscribed to.

        Returns:
            bool: True if the subscription exists, otherwise False.
        """
        query = select(Subscription).where(
            Subscription.subscriber_id == subscriber_id,
            Subscription.subscribed_to_id == subscribed_to_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def check_is_subscribed(
        self, subscriber_id: int, subscribed_to_id: int
    ) -> bool:
        """
        Check if a specific user is subscribed to another user.

        This method checks if the current user (subscriber) is subscribed to a target user.

        Args:
            subscriber_id (int): The ID of the user who is subscribing.
            subscribed_to_id (int): The ID of the user being subscribed to.

        Returns:
            bool: True if the user is subscribed, otherwise False.
        """
        query = select(Subscription).where(
            Subscription.subscriber_id == subscriber_id,
            Subscription.subscribed_to_id == subscribed_to_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def check_is_subscribed_by(
        self, subscriber_id: int, subscribed_to_id: int
    ) -> bool:
        """
        Check if the current user is being subscribed to by another user.

        This method checks if the target user (subscribed_to) is subscribed to the current user (subscriber).

        Args:
            subscriber_id (int): The ID of the user being subscribed to.
            subscribed_to_id (int): The ID of the user who is subscribing.

        Returns:
            bool: True if the current user is being subscribed to, otherwise False.
        """
        query = select(Subscription).where(
            Subscription.subscriber_id == subscribed_to_id,
            Subscription.subscribed_to_id == subscriber_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def create_subscription(
        self, subscriber_id: int, subscribed_to_id: int
    ) -> dict:
        """
        Create a new subscription between two users.

        This method allows a user to subscribe to another user. It creates a new subscription record in the database.

        Args:
            subscriber_id (int): The ID of the user who is subscribing.
            subscribed_to_id (int): The ID of the user being subscribed to.

        Returns:
            dict: A message indicating the subscription was completed successfully.
        """
        subscription = Subscription(
            subscriber_id=subscriber_id, subscribed_to_id=subscribed_to_id
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return {"message": "Subscription completed"}

    async def delete_subscription(
        self, subscriber_id: int, subscribed_to_id: int
    ) -> dict:
        """
        Cancel an existing subscription between two users.

        This method deletes a subscription between two users. If the subscription doesn't exist, an error is raised.

        Args:
            subscriber_id (int): The ID of the user who is unsubscribing.
            subscribed_to_id (int): The ID of the user being unsubscribed from.

        Raises:
            HTTPException: If the subscription is not found.

        Returns:
            dict: A message indicating the subscription was canceled.
        """
        query = select(Subscription).where(
            Subscription.subscriber_id == subscriber_id,
            Subscription.subscribed_to_id == subscribed_to_id,
        )
        result = await self.db.execute(query)
        subscription = result.scalars().first()
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found.",
            )
        await self.db.delete(subscription)
        await self.db.commit()
        return {"message": "Subscription canceled."}

    async def get_all_subscriptions(self, current_user: int) -> list:
        """
        Retrieve all users the current user is subscribed to.

        This method returns a list of users that the current user is subscribed to.

        Args:
            current_user (int): The ID of the current user.

        Returns:
            list: A list of users the current user is subscribed to.
        """
        query = (
            select(User)
            .join(Subscription, User.id == Subscription.subscribed_to_id)
            .where(Subscription.subscriber_id == current_user)
        )
        result = await self.db.execute(query)
        subscriptions = result.scalars().all()
        return subscriptions

    async def get_all_subscribers(self, current_user: int) -> list:
        """
        Retrieve all users who are subscribed to the current user.

        This method returns a list of users who are subscribed to the current user.

        Args:
            current_user (int): The ID of the current user.

        Returns:
            list: A list of users who are subscribed to the current user.
        """
        query = (
            select(User)
            .join(Subscription, User.id == Subscription.subscriber_id)
            .where(Subscription.subscribed_to_id == current_user)
        )
        result = await self.db.execute(query)
        subscribers = result.scalars().all()
        return subscribers
