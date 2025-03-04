from sqlalchemy import insert, func, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy.orm import selectinload, joinedload

from src.models.models import Photo, photo_tags, User, PhotoRating, Comment, Tag
from src.tags.repos import TagRepository

MAX_TAGS_COUNT = 5


class PhotoRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the PhotoRepository.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session

    async def create_photo(
        self, url_link: str, description: str, user: User, tags: list
    ) -> Photo:
        """
        Create a new photo with optional tags.

        Args:
            url_link (str): The URL of the photo.
            description (str): Description of the photo.
            user (User): The user who owns the photo.
            tags (list): List of tags for the photo.

        Returns:
            Photo: The created photo with its metadata.

        Raises:
            HTTPException: If more than 5 tags are provided or an SQL error occurs.
        """
        try:

            new_photo = Photo(
                url_link=url_link, description=description, owner_id=user.id
            )
            self.session.add(new_photo)
            await self.session.commit()  # Отримуємо ID фото
            await self.session.refresh(new_photo)
            if len(tags) > 5:
                print("You can add only 5 tags, tags 6 and above will be ignored")

            tags = tags[:MAX_TAGS_COUNT]
            tag_repo = TagRepository(self.session)
            tag_ids = []

            for tag_name in tags:

                tag = await tag_repo.create_tag(tag_name)
                tag_ids.append(tag.id)

            if tag_ids:
                for tag_id in tag_ids:

                    await self.session.refresh(new_photo)
                    existing_relation = await self.session.execute(
                        select(photo_tags).filter_by(
                            photo_id=new_photo.id, tag_id=tag_id
                        )
                    )
                    if not existing_relation.scalar():
                        stmt = insert(photo_tags).values(
                            photo_id=new_photo.id, tag_id=tag_id
                        )
                        await self.session.execute(stmt)

            await self.session.commit()
            await self.session.refresh(new_photo)
            return new_photo

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_photo_by_id(self, photo_id: int) -> Photo:
        """
        Retrieve a photo by its ID.

        Args:
            photo_id (int): The ID of the photo.

        Returns:
            Photo: The photo object if found, else None.
        """
        result = await self.session.execute(select(Photo).filter(Photo.id == photo_id))
        photo = result.scalar_one_or_none()
        if photo:
            return photo
        else:
            raise HTTPException(status_code=404, detail="Photo not found")

    async def update_photo_description(
        self, photo_id: int, description: str, user_id: int
    ) -> Photo:
        """
        Update the description of a photo.

        Args:
            photo_id (int): The ID of the photo.
            description (str): The new description.
            user_id (int): The ID of the user making the request.

        Returns:
            Photo: The updated photo object.

        Raises:
            HTTPException: If the photo does not exist or the user is not the owner.
        """
        photo = await self.get_photo_by_id(photo_id)

        if photo is None:
            raise HTTPException(status_code=404, detail="Rating not found")
        else:
            photo.description = description
            await self.session.commit()
            await self.session.refresh(photo)
            return photo

    async def delete_photo(self, photo_id: int) -> str:
        """
        Delete a photo by its ID.

        Args:
            photo_id (int): The ID of the photo to delete.

        Returns:
            str: A message indicating success or failure.

        Raises:
            SQLAlchemyError: If an error occurs during deletion.
        """
        try:
            query = await self.session.execute(
                select(Photo).where(Photo.id == photo_id)
            )
            photo = query.scalars().first()
            if not photo:
                return None
            await self.session.delete(photo)
            await self.session.commit()
            return "Deleted"
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_users_all_photos(self, user: User) -> list[Photo]:
        query = select(Photo).where(Photo.owner_id == user.id)
        result = await self.session.execute(query)
        photos = result.scalars().all()
        if photos:
            return photos
        else:
            return None

    async def get_all_photos(self, page):

        photos_per_page = 20
        offset = (page - 1) * photos_per_page

        photos_query = (
            select(Photo.id, Photo.url_link, Photo.description, User.username, User.avatar_url)
            .join(User, Photo.owner_id == User.id)
            .order_by(desc(Photo.created_at))
            .offset(offset)
            .limit(photos_per_page)
        )

        result = await self.session.execute(photos_query)
        photos = result.all()

        photos_list = []
        photo_ids = []

        for row in photos:
            photo_id, url, description, username, avatar_url = row
            photo_ids.append(photo_id)
            photos_list.append({
                "photo_id": photo_id,
                "url_link": url,
                "description": description,
                "username": username,
                "avatar_url": avatar_url,
                "tags": [],
                "last_comment": None
            })

        if photo_ids:
            tags_query = (
                select(photo_tags.c.photo_id, Tag.name)
                .join(Tag, Tag.id == photo_tags.c.tag_id)
                .where(photo_tags.c.photo_id.in_(photo_ids))
            )

            tags_result = await self.session.execute(tags_query)

            tags_dict = {}
            for photo_id, tag_name in tags_result:
                tags_dict.setdefault(photo_id, []).append(tag_name)

            for photo in photos_list:
                photo["tags"] = tags_dict.get(photo["photo_id"], [])

            last_comments_query = (
                select(Comment.photo_id, Comment.content, User.username)
                .join(User, Comment.user_id == User.id)
                .where(Comment.photo_id.in_(photo_ids))
                .order_by(Comment.photo_id, desc(Comment.created_at))
            )

            comments_result = await self.session.execute(last_comments_query)

            last_comments_dict = {}
            for photo_id, content, comment_author in comments_result:
                if photo_id not in last_comments_dict:
                    last_comments_dict[photo_id] = {
                        "content": content,
                        "author": comment_author
                    }

            for photo in photos_list:
                photo["last_comment"] = last_comments_dict.get(photo["photo_id"])


        total_photos_query = select(func.count(Photo.id))
        total_photos_result = await self.session.execute(total_photos_query)
        total_photos = total_photos_result.scalar()

        total_pages = (total_photos + photos_per_page - 1) // photos_per_page
        print(photos_list)
        return photos_list, total_pages

    async def get_data_for_main_page(self):
        photos_query = (
            select(Photo.id, Photo.url_link, Photo.description, User.username, User.avatar_url)
            .join(User, Photo.owner_id == User.id)
            .order_by(desc(Photo.created_at))
            .limit(9)
        )

        photos = await self.session.execute(photos_query)
        photos_result = photos.all()
        print(photos_result)
        print('222222222222222222222222222222222222222222222222222222')
        comments_query = (
            select(Comment.content, Comment.photo_id, User.username, User.avatar_url)
            .join(User, Comment.user_id == User.id)
            .order_by(desc(Comment.created_at))
            .limit(3)
        )

        comments = await self.session.execute(comments_query)
        comments_result = comments.all()


        users_query = select(User.username, User.avatar_url).order_by(desc(User.created_at)).limit(3)
        users = await self.session.execute(users_query)
        users_result = users.all()

        tags_query = (
            select(Tag.name, func.count(photo_tags.c.photo_id).label("photo_count"))
            .join(photo_tags, Tag.id == photo_tags.c.tag_id)
            .group_by(Tag.id)
            .order_by(desc("photo_count"))
            .limit(6)
        )

        tags = await self.session.execute(tags_query)
        tags_result = tags.scalars().unique().all()

        return users_result, photos_result, tags_result, comments_result

    async def get_following_photos(self, users) -> list[Photo]:
        following_ids = [following_user.id for following_user in users]

        photos_query = (
            select(Photo)
            .where(Photo.owner_id.in_(following_ids))
            .order_by(Photo.created_at.desc())
            .options(joinedload(Photo.owner), joinedload(Photo.tags))
        )
        photos_result = await self.session.execute(photos_query)
        photos = photos_result.unique().scalars().all()

        return photos

class PhotoRatingRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize the PhotoRatingRepository.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session

    async def update_average_rating(self, photo_id: int) -> None:
        """
        Update the average rating for a photo.

        Args:
            photo_id (int): The ID of the photo to update.

        Raises:
            SQLAlchemyError: If an error occurs during the update.
        """
        # Calculate the average rating for a photo
        avg_rating = await self.session.scalar(
            select(func.avg(PhotoRating.rating)).where(PhotoRating.photo_id == photo_id)
        )

        # Оновлюємо поле average_rating в фото
        if avg_rating is not None:
            avg_rating = round(float(avg_rating), 2)
            photo = await self.session.scalar(select(Photo).where(Photo.id == photo_id))
            photo.rating = avg_rating
            await self.session.commit()

    async def add_and_update_rating(
        self, photo_id: int, user_id: int, rating: int
    ) -> None:
        """
        Add a rating to a photo and update the average rating.

        Args:
            photo_id (int): The ID of the photo.
            user_id (int): The ID of the user providing the rating.
            rating (int): The rating value.

        Raises:
            HTTPException: If a rating already exists for the user and photo.
        """
        # Check if the rating already exists
        existing_rating = await self.session.scalar(
            select(PhotoRating).where(
                PhotoRating.photo_id == photo_id, PhotoRating.user_id == user_id
            )
        )
        if existing_rating:
            raise HTTPException(status_code=400, detail="Rating already exists")
        else:
            new_rating = PhotoRating(photo_id=photo_id, user_id=user_id, rating=rating)
            self.session.add(new_rating)

        await self.session.commit()
        await self.update_average_rating(photo_id)

    async def get_rating(self, photo_id: int, user_id: int):
        """
        Retrieve a specific user's rating for a photo.

        Args:
            photo_id (int): The ID of the photo.
            user_id (int): The ID of the user.

        Returns:
            int: The rating value if it exists, else None.
        """
        rating = await self.session.scalar(
            select(PhotoRating.rating).where(
                PhotoRating.photo_id == photo_id, PhotoRating.user_id == user_id
            )
        )
        return rating

    async def delete_rating(self, photo_id: int, user_id: int) -> None:
        """
        Delete a specific user's rating for a photo.

        Args:
            photo_id (int): The ID of the photo.
            user_id (int): The ID of the user.

        Raises:
            HTTPException: If the rating does not exist.
        """
        # Check if a rating exists for this user
        rating = await self.session.scalar(
            select(PhotoRating).where(
                PhotoRating.photo_id == photo_id, PhotoRating.user_id == user_id
            )
        )
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found")

        await self.session.delete(rating)
        await self.session.commit()

        await self.update_average_rating(photo_id)

    async def get_ratings_by_photo_id(self, photo_id: int):
        """
        Retrieve all ratings for a specific photo.

        Args:
            photo_id (int): The ID of the photo.

        Returns:
            list[PhotoRating]: A list of ratings for the photo.
        """
        get_rating = await self.session.execute(
            select(PhotoRating).where(PhotoRating.photo_id == photo_id)
        )

        return get_rating.scalars().all()

    async def get_ratings_by_user_id(self, user_id: int):
        """
        Retrieve all ratings provided by a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[PhotoRating]: A list of ratings provided by the user.
        """
        get_rating = await self.session.execute(
            select(PhotoRating).where(PhotoRating.user_id == user_id)
        )
        return get_rating.scalars().all()

    async def get_average_rating(self, photo_id: int):
        """
        Retrieve the average rating for a photo.

        Args:
            photo_id (int): The ID of the photo.

        Returns:
            float: The average rating value.
        """
        get_average_rating = await self.session.execute(
            select(Photo.rating).where(Photo.id == photo_id)
        )
        return get_average_rating.scalar()


