from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from src.auth.repos import UserRepository
from src.auth.utils import decode_access_token
from src.models.models import Photo, User
from src.models.models import Comment
from src.tags.repos import TagRepository


class TagWebRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_photos(self):
        photos = await self.db.execute(select(Photo).order_by(desc(Photo.created_at)))
        result = photos.scalars().all()
        print("Photos:", result)
        return result

    async def get_data_for_main_page(self):
        tag_repo = TagRepository(self.db)

        users = await self.db.execute(select(User))
        photos = await self.get_all_photos()
        popular_tags = await tag_repo.get_all_tags()
        popular_users = users.scalars().all()
        recent_comments = await self.get_all_commets()

        return users, photos, popular_tags, popular_users, recent_comments

    async def get_all_commets(self):
        commets = await self.db.execute(select(Comment))
        return commets.scalars().all()

    async def get_current_user_cookies(self, request):
        token = request.cookies.get("access_token")
        if token:
            user = decode_access_token(token)
        else:
            return None
        if user is not None:
            user_repo = UserRepository(self.db)
            user = await user_repo.get_user_by_username(user.username)

        return user
