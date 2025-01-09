"""
This module contains the `UserProfileRepository` class, which provides methods for managing user profiles 
in a database using SQLAlchemy with asynchronous operations. It includes functionality for updating user profiles, 
retrieving user data, and banning/unbanning users.

Classes:
    - UserProfileRepository: A repository for performing operations on user profiles in the database.

Dependencies:
    - sqlalchemy: For database interactions.
    - src.models.models: Contains the User model definition.
    - src.user_profile.schemas: Defines the schema for user profile updates.
    - src.auth.repos: Provides utility functions for user-related database operations.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User
from src.user_profile.schemas import UserProfileUpdate
from src.auth.repos import UserRepository


class UserProfileRepository:
    """
    A repository class for managing user profiles in the database.

    Methods:
        - update_user: Updates user profile details in the database.
        - get_user: Retrieves a user by their username.
        - ban_user: Bans a user by setting the `is_banned` flag to True.
        - unban_user: Unbans a user by setting the `is_banned` flag to False.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the UserProfileRepository with a database session.

        Args:
            session (AsyncSession): The asynchronous SQLAlchemy session to interact with the database.
        """
        self.session = session

    async def update_user(self, user_id: int, user_update: UserProfileUpdate) -> User:
        """
        Updates the user profile with the given user ID using the provided update data.

        Args:
            user_id (int): The ID of the user to update.
            user_update (UserProfileUpdate): An object containing the updated user details.

        Returns:
            User: The updated user object, or None if the user does not exist.
        """
        user = await UserRepository.get_user_by_id(self, user_id)
        if not user:
            return None
        if user_update.username is not None:
            user.username = user_update.username
        if user_update.first_name is not None:
            user.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.last_name = user_update.last_name
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.birth_date is not None:
            user.birth_date = user_update.birth_date
        if user_update.country is not None:
            user.country = user_update.country
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user(self, username: str) -> User:
        """
        Retrieves a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User: The user object, or None if no user with the given username exists.
        """
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar()

    async def ban_user(self, username: str) -> User:
        """
        Bans a user by setting their `is_banned` flag to True.

        Args:
            username (str): The username of the user to ban.

        Returns:
            User: The banned user object, or None if the user does not exist.
        """
        user = await UserRepository.get_user_by_username(self, username)
        if not user:
            return None
        if user.is_banned:
            return user
        user.is_banned = True
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def unban_user(self, username: str) -> User:
        """
        Unbans a user by setting their `is_banned` flag to False.

        Args:
            username (str): The username of the user to unban.

        Returns:
            User: The unbanned user object, or None if the user does not exist.
        """
        user = await UserRepository.get_user_by_username(self, username)
        if not user:
            return None
        user.is_banned = False
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
