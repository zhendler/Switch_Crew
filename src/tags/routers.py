from sqlalchemy.ext.asyncio import AsyncSession
from .repos import TagRepository
from config.db import get_db
from fastapi import Depends, APIRouter, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from .schemas import TagResponse
from ..auth.utils import RoleChecker, get_current_user
from src.auth.schemas import RoleEnum
from ..auth.utils import FORALL, FORMODER, check_user_active, check_user_banned
from ..photos.schemas import PhotoResponse

tag_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@tag_router.post("/create/",
                 summary="Create a new tag",
                 description="""This endpoint creates a new tag with the specified name.
    The tag name should be unique and must not exceed 50 characters.""", status_code=status.HTTP_201_CREATED, response_model=TagResponse, dependencies=FORALL)
async def create_tag(tag_name: str = Form(...), db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    await tag_repo.create_tag(tag_name=tag_name)
    return await tag_repo.get_tag_by_name(tag_name)


@tag_router.get('/',
                summary="Get all tags",
                description="""This endpoint retrieves all tags stored in the database.
    It returns a list of all tag objects.""", response_model=list[TagResponse])
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    return await tag_repo.get_all_tags()


@tag_router.get('/{tag_name}/',
                summary="Get a tag by name",
                description="""This endpoint retrieves a tag by its name. 
    The tag_name should be the exact name of the tag you're looking for.""",
                response_model=TagResponse)
async def get_tag_by_name(tag_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    return await tag_repo.get_tag_by_name(tag_name)


@tag_router.delete('/admin/delete/',
                   summary="Delete a tag by name",
                   description="""This endpoint deletes a tag from the database by its name. 
    If the tag is not found, an error message is returned.""", dependencies=FORMODER)
async def delete_tag_by_name(tag_name: str = Form(...), db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    await tag_repo.delete_tag_by_name(tag_name)
    return JSONResponse(content={"detail": f"Tag {tag_name} deleted"}, status_code=200)


@tag_router.put('/admin/update/{tag_name}-{tag_new_name}/',
                summary="Update an existing tag's name",
                description="""This endpoint updates the name of an existing tag.
    You need to provide the current name and the new name for the tag.""",
                response_model=TagResponse, dependencies=FORMODER)
async def update_tag_name(tag_name: str, tag_new_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    return await tag_repo.update_tag_name(tag_name, tag_new_name)


@tag_router.get('/{tag_name}/photos/', response_model=list[PhotoResponse])
async def get_photos_by_tag(tag_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    return await tag_repo.get_photos_by_tag(tag_name)
