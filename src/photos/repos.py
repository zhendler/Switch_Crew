from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.photos.models import Photo
from src.photos.schemas import PhotoCreate
import cloudinary.uploader
from fastapi import HTTPException
from src.utils.cloudinary_helper import generate_transformed_url


async def create_photo(db: AsyncSession, photo: PhotoCreate, description: str):
    new_photo = Photo(**photo.dict(), user_id=user_id)
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return new_photo


async def get_photo(db: AsyncSession, photo_id: int):
    result = await db.execute(select(Photo).filter(Photo.id == photo_id))
    return result.scalar_one_or_none()


async def update_photo_description(db: AsyncSession, photo_id: int, description: str):
    result = await db.execute(select(Photo).filter(Photo.id == photo_id))
    photo = result.scalar_one_or_none()
    if photo is None:
        return None
    photo.description = description
    await db.commit()
    await db.refresh(photo)
    return photo


async def delete_photo(db: AsyncSession, photo_id: int):
    result = await db.execute(select(Photo).filter(Photo.id == photo_id))
    photo = result.scalar_one_or_none()
    if photo is None:
        return False
    await db.delete(photo)
    await db.commit()
    return True


async def upload_photo_to_cloudinary(file_path: str):
    try:
        from asyncio import get_running_loop

        loop = get_running_loop()
        upload_result = await loop.run_in_executor(
            None, cloudinary.uploader.upload, file_path
        )
        return upload_result.get("url")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Cloudinary upload error: {str(e)}"
        )


async def create_photo(db: AsyncSession, photo: PhotoCreate, user_id: int):
    cloudinary_url = await upload_photo_to_cloudinary(photo.file_path)
    new_photo = Photo(
        user_id=user_id,
        cloudinary_url=cloudinary_url,
        description=photo.description,
        tags=photo.tags,
    )
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return new_photo


transformed_url = generate_transformed_url(
    "example.jpg", gravity="auto", height=300, width=200, crop="fill"
)
