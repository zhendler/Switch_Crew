"""
Repository layer for managing database operations related to users and roles.

This module contains two repository classes:
- `UserRepository`: Handles operations for `User` models, including creating, retrieving, updating users, managing avatars, and activating user accounts.
- `RoleRepository`: Manages operations for `Role` models, including retrieving roles by name.

Dependencies:
- SQLAlchemy: Provides ORM capabilities for database interactions.
- FastAPI: Handles HTTP exceptions and file uploads.
- Cloudinary: Manages cloud-based avatar uploads.
- Custom utilities for password hashing and schema definitions.

Classes:
    - UserRepository
    - RoleRepository
"""

from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader

from config.general import settings
from src.models.models import User, Role
from src.auth.pass_utils import get_password_hash
from src.auth.schemas import UserCreate, RoleEnum


class UserRepository:
    """
    Repository class for managing `User` data.

    Args:
        session (AsyncSession): SQLAlchemy asynchronous session for database operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_create: UserCreate):
        """
        Creates a new user in the database.

        Hashes the user's password, fetches their Gravatar avatar, and assigns the default role.

        Args:
            user_create (UserCreate): Schema containing the new user's details.

        Returns:
            User: The newly created `User` object.
        """
        hashed_password = get_password_hash(user_create.password)
        result = await self.session.execute(select(User.id).limit(1))
        first_user = result.scalars().first()
        if not first_user:
            user_role = await RoleRepository(self.session).get_role_by_name(RoleEnum.ADMIN)
        else:
            user_role = await RoleRepository(self.session).get_role_by_name(RoleEnum.USER)
        new_user = User(
            username=user_create.username,
            hashed_password=hashed_password,
            email=user_create.email,
            role_id=user_role.id,
            is_active=False,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def get_user_by_email(self, email):
        """
        Retrieves a user by their email address.

        Args:
            email (str): The email address of the user.

        Returns:
            User or None: The `User` object if found, otherwise `None`.
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str):
        """
        Retrieves a user by their username.

        Args:
            username (str): The username of the user.

        Returns:
            User or None: The `User` object if found, otherwise `None`.
        """
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int):
        """
        Retrieves a user by their unique ID.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            User or None: The `User` object if found, otherwise `None`.
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def upload_to_cloudinary(self, file: UploadFile) -> str:
        """
        Uploads a file to Cloudinary and returns the secure URL.

        Args:
            file (UploadFile): The file to upload.

        Returns:
            str: The secure URL of the uploaded file.

        Raises:
            HTTPException: If the upload fails.
        """
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True
        )
        try:
            result = cloudinary.uploader.upload(file.file)
            return result["secure_url"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload avatar: {str(e)}"
            )
    
    async def update_avatar(self, email, url: str) -> User:
        """
        Updates a user's avatar URL.

        Args:
            email (str): The user's email address.
            url (str): The new avatar URL.

        Returns:
            User: The updated `User` object.
        """
        user = await self.get_user_by_email(email)
        user.avatar_url = url
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def activate_user(self, user: User):
        """
        Activates a user account.

        Args:
            user (User): The `User` object to activate.

        Returns:
            None
        """
        user.is_active = True
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

    async def update_user_password(self, user: User, hashed_password: str):
        """
        Updates a user's password in the database.

        Args:
            user (User): The `User` object whose password needs updating.
            hashed_password (str): The new hashed password.

        Returns:
            None
        """
        user.hashed_password = hashed_password
        await self.session.commit()


class RoleRepository():
    """
    Repository class for managing `Role` data.

    Args:
        session (AsyncSession): SQLAlchemy asynchronous session for database operations.
    """

    def __init__(self, session):
        self.session = session

    async def get_role_by_name(self, name: RoleEnum):
        """
        Retrieves a role by its name.

        Args:
            name (RoleEnum): The name of the role to retrieve.

        Returns:
            Role or None: The `Role` object if found, otherwise `None`.
        """
        query = select(Role).where(Role.name == name.value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()