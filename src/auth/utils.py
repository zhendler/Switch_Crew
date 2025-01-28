"""
This module provides utility functions and dependencies for authentication, token management, and role-based access control using FastAPI.

It includes:
- JWT token creation and decoding for verification, access, and refresh tokens.
- Dependency functions for retrieving and validating the current user.
- Role-based access control using a RoleChecker dependency.
- User status checks for active and banned accounts.
"""

from fastapi import Depends, status, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from src.auth.schemas import TokenData, RoleEnum
from src.auth.repos import UserRepository
from src.models.models import User
from config.general import settings
from config.db import get_db

ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
VERIFICATION_TOKEN_EXPIRE_HOURS = settings.verification_token_expire_hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_verification_token(email: str) -> str:
    """
    Creates a verification token for user email verification.

    Args:
        email (str): The user's email address.

    Returns:
        str: A signed JWT token containing the email and expiration time.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        hours=VERIFICATION_TOKEN_EXPIRE_HOURS
    )
    to_encode = {"exp": expire, "sub": email}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_verification_token(token: str) -> str | None:
    """
    Decodes a verification token to extract the email.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[str]: The email if valid, or None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def create_access_token(data: dict):
    """
    Creates an access token.

    Args:
        data (dict): Data to include in the token payload.

    Returns:
        str: A signed JWT token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encode_jwt


def create_refresh_token(data: dict):
    """
    Creates a refresh token.

    Args:
        data (dict): Data to include in the token payload.

    Returns:
        str: A signed JWT token with an extended expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encode_jwt


def decode_access_token(token: str) -> TokenData | None:
    """
    Decodes an access token to extract user information.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[TokenData]: Token data if valid, or None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Retrieves the current user based on the access token.

    Args:
        token (str): The access token.
        db (AsyncSession): The database session.

    Returns:
        User: The current authenticated user.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def check_user_active(current_user: User = Depends(get_current_user)) -> None:
    """
    Checks if the current user's account is active.

    Args:
        current_user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user account is not active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please activate your account first.",
        )


async def check_user_banned(user: User = Depends(get_current_user)) -> None:
    """
    Checks if the current user's account is banned.

    Args:
        user (User): The currently authenticated user.

    Raises:
        HTTPException: If the user account is banned.
    """
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been banned. Please contact the administrator.",
        )


class RoleChecker:
    """
    Dependency for checking user roles.

    Args:
        allowed_roles (list[RoleEnum]): A list of roles allowed to access the resource.
    """

    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ) -> User:
        """
        Checks if the user has the required role to access a resource.

        Args:
            token (str): The access token.
            db (AsyncSession): The database session.

        Returns:
            User: The current authenticated user.

        Raises:
            HTTPException: If the user does not have the required role.
        """
        user = await get_current_user(token, db)
        is_admin_or_moderator = user.role.name in [
            RoleEnum.ADMIN.value,
            RoleEnum.MODERATOR.value,
        ]
        if user.role.name not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user, is_admin_or_moderator


FORADMIN = [Depends(RoleChecker([RoleEnum.ADMIN]))]
FORMODER = [Depends(RoleChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR]))]
FORALL = [Depends(RoleChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR, RoleEnum.USER]))]
ACTIVATE = [Depends(check_user_active)]
BANNED_CHECK = [Depends(check_user_banned)]
ACTIV_AND_BANNED = [Depends(check_user_active), Depends(check_user_banned)]
