from sqlalchemy import insert, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.models import Photo, photo_tags, User, PhotoRating
from src.photos.schemas import PhotoCreate, PhotoResponse
from fastapi import HTTPException, UploadFile

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
            # Add a new photo
            new_photo = Photo(
                url_link=url_link, description=description, owner_id=user.id
            )
            self.session.add(new_photo)
            await self.session.commit()  # Get the photo ID
            await self.session.refresh(new_photo)
            if len(tags) > 5:

                raise HTTPException(
                    status_code=400,
                    detail="You can add only 5 tags, tags 6 and above will be ignored",
                )
            tags = tags[:MAX_TAGS_COUNT]
            tag_repo = TagRepository(self.session)
            tag_ids = []

            # Get or create tags
            for tag_name in tags:
                # Get or create a tag, avoiding duplication
                tag = await tag_repo.create_tag(tag_name)
                tag_ids.append(tag.id)

            # Add links between photos and tags
            if tag_ids:
                for tag_id in tag_ids:
                    # Check for an entry in the intermediate table
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

            # Commit to change
            await self.session.commit()
            await self.session.refresh(new_photo)
            return new_photo



    async def get_photo_by_id(self, photo_id: int) -> Photo:
        """
        Retrieve a photo by its ID.

        Args:
            photo_id (int): The ID of the photo.

        Returns:
            Photo: The photo object if found, else None.
        """
        result = await self.session.execute(select(Photo).filter(Photo.id == photo_id))
        return result.scalar_one_or_none()

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
        photo = await self.session.get(Photo, photo_id)

        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        if photo.owner_id != user_id:
            raise HTTPException(
                status_code=403, detail="You are not the owner of this photo"
            )
        photo.description = description
        await self.session.commit()
        await self.session.refresh(photo)
        return photo

    async def delete_photo(self, photo_id: int):
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

    async def get_users_all_photos(self, user):
        """
        Retrieve all photos uploaded by a specific user.

        Args:
            user (User): The user whose photos to retrieve.

        Returns:
            list[Photo]: A list of photos uploaded by the user.
        """
        query = select(Photo).where(Photo.owner_id == user.id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_photos(self, user):
        """
        Retrieve all photos in the database.

        Returns:
            list[Photo]: A list of all photos in the database.
        """
        query = select(Photo)
        result = await self.session.execute(query)
        return result.scalars().all()


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
        # Update the average_rating field in the photo
        if avg_rating is not None:
            avg_rating = round(float(avg_rating), 2)
            print(avg_rating)
            print ("________________________________________________________________________________")
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

    async def get_rating(self, photo_id, user_id):
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
