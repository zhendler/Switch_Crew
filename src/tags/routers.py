from sqlalchemy.ext.asyncio import AsyncSession
from .repos import TagRepository
from config.db import get_db
from fastapi import Depends, APIRouter

tag_router = APIRouter()

@tag_router.post("/create/")
async def create_tag(name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.create_tag(name=name)
    return tag

@tag_router.get('/')
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    return await tag_repo.get_all_tags()

@tag_router.get('/{tag_name}/')
async def get_tag_by_name(tag_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.get_tag_by_name(tag_name)
    return tag

@tag_router.delete('/delete/{tag_name}/')
async def delete_tag_by_name(tag_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.delete_tag_by_name(tag_name)
    return tag

@tag_router.put('/update/{tag_name}-{tag_new_name}/')
async def update_tag_name(tag_name: str, tag_new_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.update_tag_name(tag_name, tag_new_name)
    return tag

# @tag_router.get('/{tag_name}/photos/')
# async def get_photos_by_tag(tag_name: str, db: Session = Depends(get_db)):
#     tag_repo = TagRepository(db)
#     photos = await tag_repo.get_photos_by_tag(tag_name)
#     return photos
