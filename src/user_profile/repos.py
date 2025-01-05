
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User
from src.user_profile.schemas import UserProfileUpdate
from src.auth.repos import UserRepository


class UserProfileRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_user(self, user_id: int, user_update: UserProfileUpdate) -> User:
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
    
    async def get_user(self, username: int) -> User:
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar()
    
    async def ban_user(self, username: str) -> User:
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
        user = await UserRepository.get_user_by_username(self, username)
        if not user:
            return None
        user.is_banned = False
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user