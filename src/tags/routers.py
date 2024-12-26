from sqlalchemy.ext.asyncio import AsyncSession
from .repos import TagRepository
from config.db import get_db
from fastapi import Depends, APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

tag_router = APIRouter()
templates = Jinja2Templates(directory="templates")


# @tag_router.post("/create/")
# async def create_tag2(tag_name: str = Form(...)):
#     return RedirectResponse(f"/tags/create/{tag_name}/", status_code=303)

@tag_router.post("/create/",
                 summary="Create a new tag",
                 description="""This endpoint creates a new tag with the specified name.
    The tag name should be unique and must not exceed 50 characters.""")
async def create_tag(tag_name: str = Form(...), db: AsyncSession = Depends(get_db)):
    """
    Creates a new tag.

    - **name**: The name of the tag to create.
    - **db**: The database session provided by FastAPI dependency injection (optional).

    Returns:
    - The created tag object.
    """
    tag_repo = TagRepository(db)
    await tag_repo.create_tag(name=tag_name)
    return RedirectResponse("/tags/", status_code=302)


@tag_router.get('/',
                summary="Get all tags",
                description="""This endpoint retrieves all tags stored in the database.
    It returns a list of all tag objects.""")
async def get_all_tags(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Retrieves all tags.

    - **db**: The database session provided by FastAPI dependency injection (optional).

    Returns:
    - A list of all tag objects.
    """
    tag_repo = TagRepository(db)
    tags = await tag_repo.get_all_tags()
    return templates.TemplateResponse("tags.html", {"request": request, "title": "Tags", "tags": tags})


@tag_router.get('/{tag_name}/',
                summary="Get a tag by name",
                description="""This endpoint retrieves a tag by its name. 
    The `tag_name` should be the exact name of the tag you're looking for.""")
async def get_tag_by_name(tag_name: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a tag by its name.

    - **tag_name**: The name of the tag to retrieve.
    - **db**: The database session provided by FastAPI dependency injection (optional).

    Returns:
    - The tag object if found, or `None` if not.
    """
    tag_repo = TagRepository(db)
    tag = await tag_repo.get_tag_by_name(tag_name)
    return tag


@tag_router.delete('/delete/{tag_name}/',
                   summary="Delete a tag by name",
                   description="""This endpoint deletes a tag from the database by its name. 
    If the tag is not found, an error message is returned.""")
async def delete_tag_by_name(tag_name: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a tag by its name.

    - **tag_name**: The name of the tag to delete.
    - **db**: The database session provided by FastAPI dependency injection (optional).

    Returns:
    - A success message if the tag was deleted, or an error message if the tag was not found.
    """
    tag_repo = TagRepository(db)
    tag = await tag_repo.delete_tag_by_name(tag_name)
    return tag


@tag_router.put('/update/{tag_name}-{tag_new_name}/',
                summary="Update an existing tag's name",
                description="""This endpoint updates the name of an existing tag.
    You need to provide the current name and the new name for the tag.""")
async def update_tag_name(tag_name: str, tag_new_name: str, db: AsyncSession = Depends(get_db)):
    """
    Updates the name of an existing tag.

    - **tag_name**: The current name of the tag to update.
    - **tag_new_name**: The new name to assign to the tag.
    - **db**: The database session provided by FastAPI dependency injection (optional).

    Returns:
    - The updated tag object if successful, or an HTTPException with status 404 if the tag is not found.
    """
    tag_repo = TagRepository(db)
    tag = await tag_repo.update_tag_name(tag_name, tag_new_name)
    return tag


@tag_router.get('/{tag_name}/photos/')
async def get_photos_by_tag(request: Request, tag_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    photos = await tag_repo.get_photos_by_tag(tag_name)
    if photos:
        return templates.TemplateResponse("photos_by_tag.html", {"request": request, "title": tag_name.capitalize(), "photos": photos})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "title": "Home Page"})

"""
Usage:
------
This router can be included in a FastAPI app to provide tag management functionality. 
Example:

    from fastapi import FastAPI
    from your_module.tag_router import tag_router

    app = FastAPI()
    app.include_router(tag_router, prefix="/tags", tags=["Tags"])
"""