from fileinput import close

import select
from sqlalchemy.future import select
from tempfile import NamedTemporaryFile
import cloudinary
from config.db import get_db
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
import os
from src.auth.schemas import RoleEnum
from src.auth.utils import RoleChecker, decode_access_token
from src.models.models import Photo, Tag, photo_tags, User
from src.photos.repos import (
    delete_photo,
    get_photo,
    update_photo_description,
    upload_photo_to_cloudinary,
)
from src.photos.schemas import PhotoCreate, PhotoResponse, PhotoUpdate
from src.photos.schemas import TransformRequest, TransformResponse
from src.tags.repos import TagRepository
from src.tags.routers import create_tag, get_tag_by_name
from src.utils.cloudinary_helper import generate_transformed_image_url
from src.utils.qr_code_helper import generate_qr_code
from typing import Optional, List
from sqlalchemy import insert
from fastapi.templating import Jinja2Templates

photo_router = APIRouter()


@photo_router.post("/")
async def upload_photo(
    description: str = Form(...),
    tags: Optional[List[str]] = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(RoleChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR, RoleEnum.USER])),
    db: AsyncSession = Depends(get_db)
):

    if len(tags) > 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 tags allowed")
    try:
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file.file.read())
            tmp_file_path = tmp_file.name
            cloudinary_url = await upload_photo_to_cloudinary(tmp_file_path)
    except Exception as e:
        os.remove(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading to Cloudinary: {str(e)}")
    finally:
        tmp_file.close()


    qr_core_url = generate_qr_code(cloudinary_url)
    new_photo = Photo(url_link=cloudinary_url, description=description, owner_id=user[0].id, qr_core_url=qr_core_url)

    tags = [tag.strip('"') for tag in tags[0].strip('[]').split(',')]
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    tag_repo = TagRepository(db)
    if tags:
        for tag in tags:
            new_tag = await tag_repo.get_tag_by_name(tag)
            if new_tag:
                await db.refresh(new_photo)
                await db.refresh(new_tag)
                stmt = insert(photo_tags).values(photo_id=new_photo.id, tag_id=new_tag.id)
                await db.execute(stmt)
            else:
                tag = await tag_repo.create_tag(tag)
                await db.refresh(new_photo)
                await db.refresh(tag)
                stmt = insert(photo_tags).values(photo_id=new_photo.id, tag_id=tag.id)
                await db.execute(stmt)

    await db.commit()
    await db.refresh(new_photo)
    data = {
        'photo_id': new_photo.id,
        'owner_id': new_photo.owner_id,
        'description': new_photo.description,
        'tags': new_photo.tags,
        'url_link': new_photo.url_link
    }

    if os.path.exists(tmp_file_path):
        os.remove(tmp_file_path)


    return data


@photo_router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo_by_id(photo_id: int, db: AsyncSession = Depends(get_db)):
    db_photo = get_photo(db, photo_id)
    if db_photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo


@photo_router.put("/{photo_id}", response_model=PhotoResponse)
def update_photo_description_endpoint(
    photo_id: int,
    photo: PhotoUpdate,
    db: AsyncSession = Depends(get_db),
    description: str = None,
):
    update_photo = update_photo_description(db, photo_id, photo.description)
    return update_photo



@photo_router.delete("/{photo_id}")
def delete_photo_by_id(photo_id: int, db: AsyncSession = Depends(get_db)):
    delete_photo(db, photo_id)
    return {"message": "Photo deleted successfully"}


@photo_router.post("/transform", response_model=TransformResponse)
async def transform_photo(request: TransformRequest, db: AsyncSession = Depends(get_db)):
    photo = select(Photo).filter(Photo.id == request.photo_id)
    result = await db.execute(photo)
    photo = result.scalars().first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    transformed_url = generate_transformed_image_url(
        public_id=photo.url_link.split("/")[-1].split(".")[0],
        width=request.width,
        height=request.height,
        crop_mode=request.crop_mode
    )

    qr_code_url = generate_qr_code(transformed_url)

    photo.transformed_url = transformed_url
    photo.qr_code_url = qr_code_url
    await db.commit()
    await db.refresh(photo)

    return {
        "photo_id": photo.id,
        "transformed_url": photo.transformed_url,
        "qr_code_url": photo.qr_code_url
    }


templates = Jinja2Templates(directory="templates")


@photo_router.get('/photos/')
async def get_all_photos_html(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    user = decode_access_token(token)
    tag_repo = TagRepository(db)
    photos = await tag_repo.get_all_photos_html()
    if photos:
        return templates.TemplateResponse("photos_by_tag.html",
                                          {"request": request, "title": 'Photos', "photos": photos,"user": user})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "title": "Home Page","user": user})
