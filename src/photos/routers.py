import select
from sqlalchemy.future import select
import cloudinary
from config.db import get_db
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from src.models.models import Photo, Tag
from src.photos.repos import (
    delete_photo,
    get_photo,
    update_photo_description,
    upload_photo_to_cloudinary,
)
from src.photos.schemas import PhotoCreate, PhotoResponse, PhotoUpdate
from src.photos.schemas import TransformRequest, TransformResponse
from src.utils.cloudinary_helper import generate_transformed_image_url
from src.utils.qr_code_helper import generate_qr_code

photo_router = APIRouter()


@photo_router.post("/", response_model=PhotoResponse)
async def upload_photo(
    photo: PhotoCreate, file: UploadFile, db: Session = Depends(get_db)
):
    if len(photo.tags) > 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 tags allowed")
    try:
        file_path = f"photos/{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        cloudinary_url = await upload_photo_to_cloudinary(file_path)
    finally:
        import os

        if os.path.exists(file_path):
            os.remove(file_path)

    new_photo = Photo(url=cloudinary_url, description=photo.description)
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    for tag_name in photo.tags:
        tag = db.execute(select(Tag).where(Tag.name == tag_name))
        tag = tag.scalars().first()
        if tag is None:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)

        new_photo.tags.append(tag)

    db.commit()
    db.refresh(new_photo)
    return new_photo


@photo_router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo_by_id(photo_id: int, db: Session = Depends(get_db)):
    db_photo = get_photo(db, photo_id)
    if db_photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo


@photo_router.put("/{photo_id}", response_model=PhotoResponse)
def update_photo_description_endpoint(
    photo_id: int,
    photo: PhotoUpdate,
    db: Session = Depends(get_db),
    description: str = None,
):
    update_photo = update_photo_description(db, photo_id, photo.description)
    return update_photo



@photo_router.delete("/{photo_id}")
def delete_photo_by_id(photo_id: int, db: Session = Depends(get_db)):
    delete_photo(db, photo_id)
    return {"message": "Photo deleted successfully"}


@photo_router.post("/transform", response_model=TransformResponse)
async def transform_photo(request: TransformRequest, db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(photo)

    return {
        "photo_id": photo.id,
        "transformed_url": photo.transformed_url,
        "qr_code_url": photo.qr_code_url
    }