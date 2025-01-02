from http.client import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.models import Tag, Photo
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

class TagRepository:
    """
    TagRepository
    -------------

    This repository class provides an interface for performing database operations related to the `Tag` model.

    Methods:
    --------

    1. **`__init__(db: AsyncSession)`**
        - Initializes the repository with an asynchronous database session.
        - Parameters:
            - `db` (AsyncSession): The SQLAlchemy asynchronous session for database operations.

    2. **`get_tag_by_name(tag_name: str)`**
        - Retrieves a tag by its name.
        - Parameters:
            - `tag_name` (str): The name of the tag to retrieve.
        - Returns:
            - `Tag` object if the tag exists, or `None` if not found.

    3. **`create_tag(name: str)`**
        - Creates a new tag with the specified name.
        - Parameters:
            - `name` (str): The name of the tag to create.
        - Returns:
            - The newly created `Tag` object.

    4. **`get_all_tags()`**
        - Retrieves all tags from the database.
        - Returns:
            - A list of all `Tag` objects.

    5. **`delete_tag_by_name(tag_name: str)`**
        - Deletes a tag by its name.
        - Parameters:
            - `tag_name` (str): The name of the tag to delete.
        - Returns:
            - A success message if the tag was deleted, or an error message if the tag was not found.

    6. **`update_tag_name(tag_name: str, tag_new_name: str)`**
        - Updates the name of an existing tag.
        - Parameters:
            - `tag_name` (str): The current name of the tag.
            - `tag_new_name` (str): The new name to assign to the tag.
        - Returns:
            - The updated `Tag` object if successful, or raises an `HTTPException` with status 404 if the tag is not found.

    7. **`get_photos_by_tag(tag_name: str)`**
        - Retrieves all photos associated with a specific tag.
        - Parameters:
            - `tag_name` (str): The name of the tag whose photos to retrieve.
        - Returns:
            - A list of photos linked to the specified tag.

    Usage:
    ------
    This repository class abstracts database interactions for the `Tag` model, enabling efficient tag management.
    Example usage:

        async def example():
            repository = TagRepository(db=session)

            # Create a new tag
            tag = await repository.create_tag(name="Travel")

            # Get all tags
            tags = await repository.get_all_tags()

            # Update a tag's name
            updated_tag = await repository.update_tag_name("Travel", "Adventure")

            # Delete a tag by name
            result = await repository.delete_tag_by_name("Adventure")
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tag_by_name(self, tag_name: str):
        query = select(Tag).filter(Tag.name == tag_name)
        result = await self.db.execute(query)
        tag = result.scalars().first()
        if tag:
            return tag
        else:
            return None

    async def create_tag(self, name: str):
        existing_tag = await self.db.execute(select(Tag).where(Tag.name == name))
        existing_tag = existing_tag.scalar_one_or_none()

        if existing_tag:
            return existing_tag

        new_tag = Tag(name=name)
        self.db.add(new_tag)
        await self.db.commit()
        await self.db.refresh(new_tag)
        return new_tag

    async def get_all_tags(self):
        tags = await self.db.execute(select(Tag))
        return tags.scalars().all()

    async def delete_tag_by_name(self, tag_name: str):
        tag = select(Tag).filter(Tag.name == tag_name)
        result = await self.db.execute(tag)
        tag = result.scalars().first()
        if tag:
            await self.db.delete(tag)
            await self.db.commit()
            return "Successfully deleted!"
        else:
            return HTTPException(status_code=404, detail="Tag not found!")

    async def update_tag_name(self, tag_name: str, tag_new_name: str):
        tag = select(Tag).filter(Tag.name == tag_name)
        result = await self.db.execute(tag)
        tag = result.scalars().first()

        if tag:
            tag.name = tag_new_name
            await self.db.commit()
            await self.db.refresh(tag)
            return tag
        else:
            return HTTPException(status_code=404, detail="Tag not found!")

    async def get_photos_by_tag(self, tag_name: str):
        tag = await self.get_tag_by_name(tag_name)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found!")

        result = await self.db.execute(
            select(Photo).options(joinedload(Photo.tags)).where(Photo.id.in_([photo.id for photo in tag.photos]))
        )
        photos = result.scalars().unique().all()
        return photos

