from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import cloudinary
from fastapi import UploadFile, HTTPException

from src.auth.repos import UserRepository
from src.auth.utils import decode_access_token
from src.models.models import Photo, User, Tag, photo_tags
from src.models.models import Comment



class TagWebRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_photos(self):
        photos = await self.db.execute(select(Photo).order_by(desc(Photo.created_at)))
        result = photos.scalars().all()
        print("Photos:", result)
        return result

    async def get_data_for_main_page(self):
        photos_query = (
            select(Photo)
            .order_by(desc(Photo.created_at))
            .limit(9)
            .options(joinedload(Photo.tags), joinedload(Photo.comments))  # Подгружаем теги и комментарии
        )

        photos = await self.db.execute(photos_query)
        photos_result = photos.scalars().unique().all()  # Используем unique для устранения повторяющихся данных

        # Получаем последние 3 комментария с пользователями
        comments_query = (
            select(Comment)
            .order_by(desc(Comment.created_at))
            .limit(3)
            .options(joinedload(Comment.user))  # Подгружаем пользователя для каждого комментария
        )

        comments = await self.db.execute(comments_query)
        comments_result = comments.scalars().unique().all()  # Убираем повторяющиеся комментарии

        users_query = select(User).order_by(desc(User.created_at)).limit(3)
        users = await self.db.execute(users_query)
        users_result = users.scalars().unique().all()  # Используем unique для пользователей

        tags_query = (
            select(Tag, func.count(photo_tags.c.photo_id).label("photo_count"))
            .join(photo_tags, Tag.id == photo_tags.c.tag_id)
            .group_by(Tag.id)
            .order_by(desc("photo_count"))
            .limit(3)
        )

        tags = await self.db.execute(tags_query)
        tags_result = tags.scalars().unique().all()

        return users_result, photos_result, tags_result, comments_result

    async def get_all_commets(self):
        commets = await self.db.execute(select(Comment))
        return commets.scalars().all()

    async def get_current_user_cookies(self, request):
        token = request.cookies.get("access_token")
        print(token)
        if token:
            user = decode_access_token(token)
        else:
            return None
        if user is not None:
            user_repo = UserRepository(self.db)
            user = await user_repo.get_user_by_username(user.username)

        return user

    async def upload_photo_to_cloudinary(self, file: UploadFile):
        file.file.seek(0)
        file_bytes = file.file.read()

        try:
            response = cloudinary.uploader.upload(
                file=file_bytes,  # Передаем байты файла
                folder="user_photos/"
            )
            return response["secure_url"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

    async def get_limit_amount_of_photos(self, amount):
        photos = await self.db.execute(
            select(Photo)
            .order_by(desc(Photo.created_at))
            .limit(amount)
        )
        result = photos.scalars().all()
        print(result)
        print('111111111111111111111111111111111111111111111111111111111111111111')
        return result

    async def get_limit_amount_of_comment(self, amount):
        data = await self.db.execute(
            select(Comment)
            .order_by(desc(Comment.created_at))
            .limit(amount)
        )
        result = data.scalars().all()
        print(result)
        print('111111111111111111111111111111111111111111111111111111111111111111')
        return result

    async def get_limit_amount_of_users(self, amount):
        data = await self.db.execute(
            select(User)
            .order_by(desc(User.created_at))
            .limit(amount)
        )
        result = data.scalars().all()
        print(result)
        print('111111111111111111111111111111111111111111111111111111111111111111')
        return result

    async def get_limit_amount_of_tags(self, amount):
        data = await self.db.execute(
            select(Tag)
            .limit(amount)
        )
        result = data.scalars().all()
        print(result)
        print('111111111111111111111111111111111111111111111111111111111111111111')
        return result