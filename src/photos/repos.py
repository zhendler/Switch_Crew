from sqlalchemy import insert, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.models import Photo, photo_tags, User, PhotoRating
from src.photos.schemas import PhotoCreate, PhotoResponse
from fastapi import HTTPException, UploadFile

from src.tags.repos import TagRepository




class PhotoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_photo(self, url_link: str, description: str, user: User, tags: list ) -> PhotoResponse:
        new_photo = Photo(url_link=url_link, description=description, owner_id=user.id)
        self.session.add(new_photo)
        await self.session.commit()
        await self.session.refresh(new_photo)

        tag_repo = TagRepository(self.session)
        tag_ids = []

        for tag_name in tags:
            tag = await tag_repo.get_or_create_tag(tag_name)
            tag_ids.append(tag.id)

        # Додаємо зв'язки між фотографією та тегами
        for tag_id in tag_ids:
            stmt = insert(photo_tags).values(photo_id=new_photo.id, tag_id=tag_id)
            await self.session.execute(stmt)
        await self.session.commit()
        await self.session.refresh(new_photo)
        return new_photo



    async def get_photo_by_id(self, photo_id: int):
        result = await self.session.execute(select(Photo).filter(Photo.id == photo_id))
        return result.scalar_one_or_none()
#
#
    async def update_photo_description(self, photo_id: int, description: str):
        photo = await self.session.get(Photo, photo_id)

        if photo is None:
            return None
        photo.description = description
        await self.session.commit()
        await self.session.refresh(photo)
        return photo

    async def delete_photo(self, photo_id: int):
        try:
            query = await self.session.execute(select(Photo).where(Photo.id == photo_id))
            photo = query.scalars().first()
            if not photo:
                return None
            await self.session.delete(photo)
            await self.session.commit()
            return "Deleted"
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_all_user_photos(self, user):
        query = select(Photo).where(Photo.owner_id == user.id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_photos(self, user):
        query = select(Photo)
        result = await self.session.execute(query)
        return result.scalars().all()


class PhotoRatingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_average_rating(self, photo_id: int) -> None:
        # Обчислюємо середній рейтинг для фото
        avg_rating = await self.session.scalar(
            select(func.avg(PhotoRating.rating)).where(PhotoRating.photo_id == photo_id)
        )

        # Оновлюємо поле average_rating в фото
        if avg_rating is not None:
            avg_rating = round(float(avg_rating), 2)
            print(avg_rating)
            print ("________________________________________________________________________________")
            photo = await self.session.scalar(select(Photo).where(Photo.id == photo_id))
            photo.rating = avg_rating
            await self.session.commit()

    async def add_and_update_rating(self, photo_id: int, user_id: int, rating: int) -> None:
        # Перевіряємо, чи вже існує рейтинг
        existing_rating = await self.session.scalar(
            select(PhotoRating).where(PhotoRating.photo_id == photo_id, PhotoRating.user_id == user_id)
        )
        if existing_rating:
            raise HTTPException(status_code=400, detail="Rating already exists")
        else:
            new_rating = PhotoRating(photo_id=photo_id, user_id=user_id, rating=rating)
            self.session.add(new_rating)

        await self.session.commit()
        await self.update_average_rating(photo_id)

    async def get_rating(self, photo_id, user_id):
        rating =  await self.session.scalar(select(PhotoRating.rating)
                                            .where(PhotoRating.photo_id == photo_id,
                                                    PhotoRating.user_id == user_id))
        return rating

    async def delete_rating(self, photo_id: int, user_id: int) -> None:
        # Перевіряємо, чи існує рейтинг для цього користувача
        rating = await self.session.scalar(
            select(PhotoRating).where(PhotoRating.photo_id == photo_id,
                                      PhotoRating.user_id == user_id)
        )
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found")


        await self.session.delete(rating)
        await self.session.commit()

        await self.update_average_rating(photo_id)

    async def get_ratings_by_photo_id(self, photo_id: int):
        get_rating  = await (self.session.execute(
            select(PhotoRating).where(PhotoRating.photo_id == photo_id))
        )

        return get_rating.scalars().all()


    async def get_ratings_by_user_id(self, user_id: int):
        get_rating = await self.session.execute(
            select(PhotoRating).where(PhotoRating.user_id == user_id)
        )
        return get_rating.scalars().all()

    async def get_average_rating(self, photo_id: int):
        get_average_rating = await self.session.execute(select(Photo.rating).where(Photo.id == photo_id))
        return get_average_rating.scalar()






