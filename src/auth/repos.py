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

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_create: UserCreate):
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
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username):
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int):
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def upload_to_cloudinary(self, file: UploadFile) -> str:
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
        user = await self.get_user_by_email(email)
        user.avatar_url = url
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def activate_user(self, user: User):
        user.is_active = True
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

    async def update_user_password(self, user: User, hashed_password: str):
        user.hashed_password = hashed_password
        await self.session.commit()


class RoleRepository():

    def __init__(self, session):
        self.session = session

    async def get_role_by_name(self, name: RoleEnum):
        query = select(Role).where(Role.name == name.value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()