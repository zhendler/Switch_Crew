from sqlalchemy.ext.asyncio import AsyncSession
from .repos import TagRepository
from config.db import get_db
from fastapi import Depends, APIRouter, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from .schemas import TagResponse
from ..auth.utils import FORALL, FORMODER
from ..photos.schemas import PhotoResponse

tag_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@tag_router.post(
    "/create/",
    summary="Create a new tag",
    description="""
    Creates a new tag with the specified name. 
    The tag name must be unique and should not exceed 50 characters.
    """,
    status_code=status.HTTP_201_CREATED,
    response_model=TagResponse,
    dependencies=FORALL,
)
async def create_tag(tag_name: str = Form(...), db: AsyncSession = Depends(get_db)):
    """
    Endpoint to create a new tag.

    This endpoint allows the creation of a new tag in the database. If a tag with the same name already exists,
    it will be returned instead of creating a duplicate.

    :param tag_name: The name of the tag to create (required).
    :param db: Database session dependency.
    :return: The newly created or existing tag as a `TagResponse` model.
    """
    tag_repo = TagRepository(db)
    await tag_repo.create_tag(tag_name=tag_name)
    return await tag_repo.get_tag_by_name(tag_name)


@tag_router.get(
    '/',
    summary="Get all tags",
    description="""
    Retrieves all tags stored in the database. 
    Returns a list of tag objects with their details.
    """,
    response_model=list[TagResponse],
)
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    """
    Endpoint to fetch all tags.

    This endpoint retrieves a list of all tags stored in the database.

    :param db: Database session dependency.
    :return: A list of `TagResponse` objects representing all tags.
    """
    tag_repo = TagRepository(db)
    return await tag_repo.get_all_tags()


@tag_router.get(
    '/{tag_name}/',
    summary="Get a tag by name",
    description="""
    Retrieves a specific tag by its name. 
    The name must match exactly with the stored tag name.
    """,
    response_model=TagResponse,
)
async def get_tag_by_name(tag_name: str, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to fetch a tag by its name.

    This endpoint allows retrieving a specific tag by its unique name.

    :param tag_name: The name of the tag to retrieve (required).
    :param db: Database session dependency.
    :return: A `TagResponse` object representing the tag.
    :raises HTTPException: If the tag is not found.
    """
    tag_repo = TagRepository(db)
    return await tag_repo.get_tag_by_name(tag_name)


@tag_router.delete(
    '/admin/delete/',
    summary="Delete a tag by name",
    description="""
    Deletes a tag from the database by its name. 
    Returns an error message if the tag is not found.
    """,
    dependencies=FORMODER,
)
async def delete_tag_by_name(tag_name: str = Form(...), db: AsyncSession = Depends(get_db)):
    """
    Endpoint to delete a tag by its name.

    This endpoint deletes a tag identified by its name from the database.

    :param tag_name: The name of the tag to delete (required).
    :param db: Database session dependency.
    :return: A JSON response confirming the deletion.
    :raises HTTPException: If the tag is not found.
    """
    tag_repo = TagRepository(db)
    await tag_repo.delete_tag_by_name(tag_name)
    return JSONResponse(content={"detail": f"Tag {tag_name} deleted"}, status_code=200)


@tag_router.put(
    '/admin/update/{tag_name}-{tag_new_name}/',
    summary="Update an existing tag's name",
    description="""
    Updates the name of an existing tag. 
    Both the current and the new tag names must be provided.
    """,
    response_model=TagResponse,
    dependencies=FORMODER,
)
async def update_tag_name(tag_name: str, tag_new_name: str, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to update the name of an existing tag.

    This endpoint allows modifying the name of a tag. The tag must exist in the database.

    :param tag_name: The current name of the tag to update (required).
    :param tag_new_name: The new name to assign to the tag (required).
    :param db: Database session dependency.
    :return: A `TagResponse` object representing the updated tag.
    :raises HTTPException: If the tag is not found.
    """
    tag_repo = TagRepository(db)
    return await tag_repo.update_tag_name(tag_name, tag_new_name)


@tag_router.get(
    '/{tag_name}/photos/',
    summary="Get photos by tag",
    description="""
    Retrieves all photos associated with a specific tag. 
    The tag name must be specified, and the associated photos will be returned as a list.
    """,
    response_model=list[PhotoResponse],
)
async def get_photos_by_tag(tag_name: str, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve photos by tag name.

    This endpoint fetches all photos associated with a specific tag in the database.

    :param tag_name: The name of the tag whose photos are to be retrieved (required).
    :param db: Database session dependency.
    :return: A list of `PhotoResponse` objects representing the photos.
    :raises HTTPException: If the tag or photos are not found.
    """
    tag_repo = TagRepository(db)
    return await tag_repo.get_photos_by_tag(tag_name)
