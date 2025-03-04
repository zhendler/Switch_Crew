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

import json
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import aiofiles

from src.models.models import (
    User,
    Subscription,
    Comment,
    Reaction,
    Photo,
    photo_reactions,
)
from src.user_profile.schemas import UserProfileUpdate, PopularUsersResponse
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

    async def search_users(self, text: str) -> list[User]:
        """
        Searches for users whose username matches the given string case-insensitively.

        Args:
            text (str): The search string

        Returns:
            list[User]: Matching users, sorted with prefix matches first
        """
        text = text.lower()
        print("2322222222222222222222222222222")
        print(text)
        query = (
            select(User)
            .where(
                or_(User.username.ilike(f"{text}%"), User.username.ilike(f"%{text}%"))
            )
            .order_by(desc(User.username.ilike(f"{text}%")))
        )

        result = await self.session.execute(query)
        users = result.scalars().all()
        print("2222222222222222222222222222222222222223")
        print(users)
        return users


class PopularUsersRepository:
    """
    Repository for retrieving and calculating the popularity of users
    based on various engagement metrics.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the PopularUserRepository with a database session.

        Args:
            session (AsyncSession): The asynchronous SQLAlchemy session to interact with the database.
        """
        self.session = session

    async def find_users_by_params(self, user_id: int):
        """
        Retrieves various engagement metrics for a given user.

        Args:
            user_id (int): The ID of the user whose metrics will be fetched.

        Returns:
            dict: A dictionary containing:
                - subscribers_count (int): Number of subscribers.
                - comments_count (int): Number of comments on user's photos.
                - reactions_count (int): Number of reactions on user's photos.
                - photos_count (int): Number of photos uploaded by the user.
        """
        # Кількість підписників на користувача
        subscribers_query = select(func.count(Subscription.id)).where(
            Subscription.subscribed_to_id == user_id
        )
        subscribers_result = await self.session.execute(subscribers_query)
        subscribers_count = subscribers_result.scalar()

        # Кількість коментарів на фото користувача
        comments_query = (
            select(func.count(Comment.id))
            .join(Photo, Photo.id == Comment.photo_id)
            .where(Photo.owner_id == user_id)
        )
        comments_result = await self.session.execute(comments_query)
        comments_count = comments_result.scalar()

        # Кількість реакцій на фото користувача
        photo_reactions_alias = aliased(photo_reactions)
        reactions_query = (
            select(func.count(Reaction.id))
            .join(
                photo_reactions_alias,
                photo_reactions_alias.c.reaction_id == Reaction.id,
            )
            .join(Photo, Photo.id == photo_reactions_alias.c.photo_id)
            .where(Photo.owner_id == user_id)
        )
        reactions_result = await self.session.execute(reactions_query)
        reactions_count = reactions_result.scalar()

        # Кількість фото користувача
        photos_query = select(func.count(Photo.id)).where(Photo.owner_id == user_id)
        photos_result = await self.session.execute(photos_query)
        photos_count = photos_result.scalar()

        return {
            "subscribers_count": subscribers_count,
            "comments_count": comments_count,
            "reactions_count": reactions_count,
            "photos_count": photos_count,
        }

    def calculate_popularity_score(
        self,
        subscribers_count: int,
        comments_count: int,
        reactions_count: int,
        photos_count: int,
    ) -> int:
        """
        Calculates the popularity score for a user based on engagement metrics.

        Args:
            subscribers_count (int): Number of subscribers.
            comments_count (int): Number of comments on user's photos.
            reactions_count (int): Number of reactions on user's photos.
            photos_count (int): Number of photos uploaded by the user.

        Returns:
            int: The calculated popularity score.
        """
        points = {"subscribers": 10, "comments": 4, "reactions": 2, "photos": 1}
        score = (
            subscribers_count * points["subscribers"]
            + comments_count * points["comments"]
            + reactions_count * points["reactions"]
            + photos_count * points["photos"]
        )
        return score

    async def get_top_10_popular_users(self):
        """
        Retrieves the top 10 most popular users based on engagement metrics.

        Returns:
            List[PopularUsersResponse]: A list of objects containing information
            about the most popular users.
        """
        # Отримуємо всіх користувачів з бази даних
        query = select(User.id, User.username).distinct()
        result = await self.session.execute(query)
        all_users = result.all()

        # Рахуємо популярність кожного користувача
        popular_users = []
        for user_id, username in all_users:
            params = await self.find_users_by_params(user_id)
            score = self.calculate_popularity_score(
                params["subscribers_count"],
                params["comments_count"],
                params["reactions_count"],
                params["photos_count"],
            )
            popular_users.append(
                {"user_id": user_id, "username": username, "score": score}
            )
        # Сортуємо користувачів за популярністю
        popular_users.sort(key=lambda x: x["score"], reverse=True)
        top_10_users = [
            PopularUsersResponse(
                position=i + 1,
                user_id=user["user_id"],
                username=user["username"],
                score=user["score"],
                from_attributes=True,
            )
            for i, user in enumerate(popular_users[:10])
        ]
        return top_10_users

    async def get_top_all_users(self):
        """
        Retrieve and rank all users based on their popularity score.

        This method fetches all distinct users from the database, calculates their
        popularity score based on various engagement metrics, sorts them in
        descending order, and assigns ranking positions. The results are then
        stored in the 'top_users.json' file.

        Popularity score is determined using:
            - Number of subscribers
            - Number of comments
            - Number of reactions
            - Number of photos uploaded

        Returns:
            List[Dict[str, Union[int, str]]]: A list of users ranked by popularity,
            including position, user ID, username, and score.

        Raises:
            Any database-related errors or file writing issues if they occur.
        """
        # Отримуємо всіх користувачів з бази даних
        query = select(User.id, User.username).distinct()
        result = await self.session.execute(query)
        all_users = result.all()

        # Рахуємо популярність кожного користувача
        popular_users = []
        for user_id, username in all_users:
            params = await self.find_users_by_params(user_id)
            score = self.calculate_popularity_score(
                params["subscribers_count"],
                params["comments_count"],
                params["reactions_count"],
                params["photos_count"],
            )
            popular_users.append(
                {"user_id": user_id, "username": username, "score": score}
            )

        # Сортуємо користувачів за популярністю
        popular_users.sort(key=lambda x: x["score"], reverse=True)

        # Формуємо список з позиціями
        top_all_users = [
            {
                "position": i + 1,
                "user_id": user["user_id"],
                "username": user["username"],
                "score": user["score"],
            }
            for i, user in enumerate(popular_users)
        ]

        # Записуємо у JSON-файл
        async with aiofiles.open("top_users.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(top_all_users, ensure_ascii=False, indent=4))

        return top_all_users

    async def update_top_all_users(self):
        """
        Update the 'top_users.json' file with the latest user rankings from the database.

        This method reads the existing user ranking data from 'top_users.json' and
        compares it with the latest data fetched from the database. It updates
        user scores if they have changed, adds new users, and removes users who
        are no longer present in the database. If any modifications occur, the
        file is rewritten with the updated rankings.

        Returns:
            List[Dict[str, Union[int, str]]]: An updated list of users with their
            ranking positions, user IDs, usernames, and scores.

        Raises:
            Any file-related or database-related errors if they occur.
        """
        file_path = "top_users.json"

        # Зчитуємо дані з файлу
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            from_json_top = json.loads(await f.read())

        # Отримуємо поточні дані з БД
        from_db_top = await self.get_top_all_users()

        # Створюємо словники для зручного порівняння даних
        json_users_dict = {user["user_id"]: user for user in from_json_top}
        db_users_dict = {user["user_id"]: user for user in from_db_top}

        # Оновлюємо або додаємо нових користувачів
        for user_id, current_user in db_users_dict.items():
            # Якщо користувач є в файлі, перевіряємо, чи змінився він
            if user_id in json_users_dict:
                if db_users_dict[user_id]["score"] != current_user["score"]:
                    json_users_dict[user_id]["score"] = current_user["score"]
            else:
                # Якщо користувача немає в файлі, додаємо його
                json_users_dict[user_id] = current_user

        # Видаляємо користувачів, яких вже немає в БД
        users_to_delete = [
            user_id for user_id in json_users_dict if user_id not in db_users_dict
        ]
        for user_id in users_to_delete:
            del json_users_dict[user_id]

        # Створюємо новий список для запису
        updated_top_users = list(json_users_dict.values())

        # Перезаписуємо файл, якщо є зміни
        if updated_top_users != from_json_top:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(
                    json.dumps(updated_top_users, ensure_ascii=False, indent=4)
                )
            print("File top_users.json updated.")

        return updated_top_users
