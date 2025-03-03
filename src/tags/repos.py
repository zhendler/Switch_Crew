from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

from ..models.models import Tag, Photo


class TagRepository:
    """
    Repository for managing tags in the database.
    Provides methods to retrieve, create, update, and delete tags, as well as retrieve photos associated with a specific tag.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the TagRepository with an asynchronous database session.

        :param db: An instance of AsyncSession for interacting with the database.
        """
        self.db = db

    async def get_tag_by_name(self, tag_name: str) -> Tag:
        """
        Retrieves a tag by its name.

        This method queries the database for a tag with the given name. If the tag is found, it is returned;
        otherwise, an HTTP 404 exception is raised.

        :param tag_name: The name of the tag to retrieve.
        :return: A `Tag` object representing the retrieved tag.
        :raises HTTPException: If no tag with the specified name is found.
        """
        result = await self.db.execute(select(Tag).where(Tag.name == tag_name))
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found!")

        return tag

    async def create_tag(self, tag_name: str) -> Tag:
        """
        Creates a new tag in the database if it does not already exist.

        This method first checks if a tag with the specified name exists. If it does, the existing tag is returned.
        Otherwise, a new tag is created, saved to the database, and returned.

        :param tag_name: The name of the tag to create.
        :return: A `Tag` object representing the newly created or existing tag.
        """
        existing_tag = await self.get_tag_by_name(tag_name)
        if existing_tag:
            return existing_tag
        else:
            new_tag = Tag(name=tag_name)
            self.db.add(new_tag)
            await self.db.commit()
            await self.db.refresh(new_tag)
            return new_tag

    async def get_all_tags(self) -> Sequence[Tag]:
        """
        Retrieves all tags from the database.

        This method fetches all tags stored in the database and returns them as a list.

        :return: A sequence of `Tag` objects representing all tags in the database.
        """
        tags = await self.db.execute(select(Tag))
        if not tags:
            raise HTTPException(status_code=404, detail="Tags not found!")

        return tags.scalars().all()


    async def get_all_tags_with_photos(self) -> Sequence[Tag]:
        """
        Retrieves all tags from the database.

        This method fetches all tags stored in the database and returns them as a list.

        :return: A sequence of `Tag` objects representing all tags in the database.
        """
        result = await self.db.execute(select(Tag))
        tags = result.scalars().all()

        tags_with_photos = [tag for tag in tags if tag.photos]
        if not tags_with_photos:
            raise HTTPException(status_code=404, detail="Tags not found!")
        return tags_with_photos

    async def delete_tag_by_name(self, tag_name: str) -> str:
        """
        Deletes a tag by its name.

        This method retrieves a tag by its name and deletes it from the database. If the tag does not exist, an exception is raised.

        :param tag_name: The name of the tag to delete.
        :return: A confirmation message indicating successful deletion.
        :raises HTTPException: If the tag with the specified name does not exist.
        """
        tag = await self.get_tag_by_name(tag_name)
        if tag:
            await self.db.delete(tag)
            await self.db.commit()
            return "Successfully deleted!"
        else:
            raise HTTPException(status_code=404, detail="Tag not found!")

    async def update_tag_name(self, tag_name: str, tag_new_name: str) -> Tag:
        """
        Updates the name of an existing tag.

        This method retrieves a tag by its current name, updates its name, and saves the changes to the database.

        :param tag_name: The current name of the tag to be updated.
        :param tag_new_name: The new name for the tag.
        :return: A `Tag` object representing the updated tag.
        :raises HTTPException: If the tag with the specified name does not exist.
        """
        tag = await self.get_tag_by_name(tag_name)
        if tag:
            tag.name = tag_new_name
            await self.db.commit()
            await self.db.refresh(tag)
            return tag
        else:
            raise HTTPException(status_code=404, detail="Tag not found!")

    async def get_photos_by_tag(self, tag_name: str) -> Sequence[Photo] or str:
        """
        Retrieves all photos associated with a specific tag.

        This method fetches a tag by its name and retrieves all photos linked to that tag. If the tag or associated photos are not found, an exception is raised.

        :param tag_name: The name of the tag whose photos are to be retrieved.
        :return: A sequence of `Photo` objects representing the photos associated with the tag.
        :raises HTTPException: If the tag or associated photos are not found.
        """
        tag = await self.get_tag_by_name(tag_name)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found!")

        result = await self.db.execute(
            select(Photo)
            .options(joinedload(Photo.tags))
            .where(Photo.id.in_([photo.id for photo in tag.photos]))
        )
        photos = result.scalars().unique().all()
        if photos:
            return photos
        else:
            return "Photos not found!"
            # raise HTTPException(status_code=404, detail="Photos not found!")

    async def search_tags(self, text: str) -> list[Tag]:
        """
        Searches for users whose username starts with the given string
        or contains the string.

        Args:
            text (str): The string to search for in usernames.

        Returns:
            list[User]: A list of users matching the criteria.
        """
        text = text.lower()
        query = select(Tag).where(
            or_(
                Tag.name.like(f"{text}%"),
                Tag.name.like(f"%{text}%")
            )
        )
        result = await self.db.execute(query)
        tags = result.scalars().all()
        if not tags:
            raise HTTPException(status_code=404, detail="Tags not found!")

        tags_sorted = sorted(tags, key=lambda tag: not tag.name.startswith(text))
        return tags_sorted