from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src import Comment
from src.models.models import User, Photo


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_users(self):
        query = select(User)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_by_id(self, user_id):
        PhotoAlias = aliased(Photo)
        CommentAlias = aliased(Comment)
        query = (
            select(
                User,
                func.count(PhotoAlias.id).label("photos_count"),
                func.count(CommentAlias.id).label("comments_count"),
            )
            .outerjoin(PhotoAlias, User.id == PhotoAlias.owner_id)  # З'єднуємось з Photo за user_id
            .outerjoin(CommentAlias, User.id == CommentAlias.user_id)  # З'єднуємось з Comment за user_id
            .where(User.id == user_id)  # Фільтруємо за user_id
            .group_by(User.id)  # Групуємо за User.id
        )

        result = await self.session.execute(query)
        user_data = result.fetchone()
        if user_data:
            user = user_data[0]
            user.photos_count = user_data.photos_count
            user.comments_count = user_data.comments_count

        return user

    async def get_usernames_list(self):
       query = select(User.username)
       result = await self.session.execute(query)
       return result.scalars().all()

    async def get_all_users_comments(self, user_id: int):

        query = select(Comment).where(Comment.user_id == user_id)
        comments = await self.session.execute(query)
        return comments.scalars().all()




