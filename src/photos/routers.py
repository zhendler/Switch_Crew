
from config.db import get_db
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from cloudinary.utils import cloudinary_url
from src.auth.utils import  get_current_user, FORALL, FORMODER
from src.models.models import User
from src.photos.repos import PhotoRepository, PhotoRatingRepository
from src.photos.schemas import PhotoResponse, PhotoUpdate, UrlPhotoResponse, PhotoRatingsListResponse, \
    UserRatingsListResponse, PhotoRatingResponse, AverageRatingResponse



from src.utils.cloudinary_helper import upload_photo_to_cloudinary, get_cloudinary_image_id

from src.utils.qr_code_helper import generate_qr_code
from typing import List, Union


photo_router = APIRouter()




@photo_router.post("/", response_model=PhotoResponse,
                   status_code=status.HTTP_201_CREATED,
                   dependencies=FORALL)
async def create_photo(tags: List[str] = Query([], title="Tegs", description="Photo tags, max 5", max_items = 5),
                       description: str = Query(None, title="Опис фотографії", description="Опис фотографії"),
                       file: UploadFile = File(...),
                       user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)) -> PhotoResponse:
    cloudinary_url = await upload_photo_to_cloudinary(file)

    photo_repo = PhotoRepository(db)
    new_photo = await photo_repo.create_photo(cloudinary_url, description, user, tags)

    return new_photo


@photo_router.get("/users_all_photos",
                  response_model=list[PhotoResponse],
                  dependencies=FORALL)
async def get_all_photos(user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_users_all_photos(user)
    if not photos:
        raise HTTPException(status_code=404, detail="Photos not found")
    return photos

@photo_router.get("/all_photos",
                  response_model=list[PhotoResponse],
                  dependencies=FORALL)
async def get_all_photos(user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_all_photos(user)
    if not photos:
        raise HTTPException(status_code=404, detail="Photos not found")
    return photos

@photo_router.get("/get_url/{photo_id}",
                  response_model=UrlPhotoResponse,
                  dependencies=FORALL)
async def get_photo_url(photo_id: int = Path(..., description="ID світлини"),
                        db: AsyncSession = Depends(get_db)) -> UrlPhotoResponse:
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@photo_router.get("/{photo_id}",
                  response_model=PhotoResponse,
                  dependencies=FORALL)
async def get_photo_by_id(photo_id: int = Path(..., description="ID світлини"),
                        db: AsyncSession = Depends(get_db)) -> PhotoResponse:
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo



@photo_router.put("/update/{photo_id}",
                  response_model=PhotoResponse,
                  dependencies=FORALL)
async def update_photo_description(
                        photo_id: int,
                        photo: PhotoUpdate,
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db),
                        ):
    photo_repo = PhotoRepository(db)
    update_photo = await photo_repo.update_photo_description(photo_id, photo.description, user.id)
    return update_photo

@photo_router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=FORALL)
async def delete_own_photo(
                        photo_id: int,
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db),
                    ):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    if photo.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You can delete only your own photos")

    await photo_repo.delete_photo(photo_id)
    return {"detail": "Photo deleted successfully"}




@photo_router.get("/{photo_id}/transform",
                  dependencies=FORALL, )
async def transform_photo(
                        photo_id: int,
                        width: int = Query(None, description="Width"),
                        height: int = Query(None, description="Height"),
                        crop: str = Query(None, description="Crop mode (наприклад, 'fill', 'fit')"),
                        effect: str = Query(None, description="Effect (наприклад, 'sepia', 'grayscale')"),
                        db: AsyncSession = Depends(get_db),
                    ):
    # Отримуємо фото з бази
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")


    transformation = {
        "width": width,
        "height": height,
        "crop": crop,
        "effect": effect,
    }

    transformation = {k: v for k, v in transformation.items() if v is not None}

    image_id = get_cloudinary_image_id(photo.url_link)

    if not image_id:
        raise ValueError("Invalid Cloudinary URL")

    transformed_url, _ = cloudinary_url(image_id, transformation=transformation)

    qr_code_data = generate_qr_code(transformed_url)


    return {"original_url": photo.url_link, "transformed_url": transformed_url, "qr_code_url": qr_code_data}





@photo_router.post("/rate/{photo_id}",
                   dependencies=FORALL)
async def rate_photo(
                        photo_id: int = Path(..., description="ID світлини"),
                        rating: int = Query(..., ge=1, le=5, description="Рейтинг світлини від 1 до 5"),
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db),
                ):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if photo.owner_id == user.id:
        raise HTTPException(status_code=403, detail="You cannot rate your own photo.")

    rating_repo = PhotoRatingRepository(db)
    await rating_repo.add_and_update_rating(photo_id, user.id, rating)

    return {"detail": "Rating added successfully."}


@photo_router.get("/rating/{photo_id}",
                  response_model=AverageRatingResponse,
                  dependencies=FORALL)
async def get_current_photo_ratings(
                        photo_id: int = Path(..., description="ID світлини"),
                        db: AsyncSession = Depends(get_db),
                      ) -> AverageRatingResponse:

    rating_repo = PhotoRatingRepository(db)
    rating = await rating_repo.get_average_rating(photo_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Not rated yet")

    return  AverageRatingResponse(rating=rating)


@photo_router.delete("/admin/del_rate",
                     dependencies=FORMODER)
async def delete_photo_rating(
                        photo_id: int = Query(..., description="ID світлини, оцінку якої потрібно видалити"),
                        user_id: int = Query(..., description="ID користувача, чий рейтинг потрібно видалити"),
                        db: AsyncSession = Depends(get_db),
                          ):
    # Отримуємо фото за ID
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    rating_repo = PhotoRatingRepository(db)
    rating = await rating_repo.get_rating(photo_id, user_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    # Видалення рейтингу
    await rating_repo.delete_rating(photo_id, user_id)

    # Оновлюємо середній рейтинг
    await rating_repo.update_average_rating(photo_id)

    return {"detail": "Rating deleted successfully."}




@photo_router.get("/admin/rate",
                  dependencies=FORMODER,
                  response_model=Union[PhotoRatingsListResponse, UserRatingsListResponse, PhotoRatingResponse])
async def get_ratings_by_user_or_photo(
                        photo_id: int = Query(None, description="ID фото для перегляду всіх оцінок"),
                        user_id: int = Query(None, description="ID користувача для перегляду його оцінок"),
                        db: AsyncSession = Depends(get_db),
                ):
    rating_repo = PhotoRatingRepository(db)

    # Якщо передано тільки photo_id — показуємо всі оцінки для фото
    if photo_id and not user_id:
        ratings = await rating_repo.get_ratings_by_photo_id(photo_id)
        if not ratings:
            raise HTTPException(status_code=404, detail="No ratings found for this photo")
        return PhotoRatingsListResponse(photo_id=photo_id, ratings=ratings)

    # Якщо передано тільки user_id — показуємо всі оцінки цього користувача
    elif user_id and not photo_id:
        ratings = await rating_repo.get_ratings_by_user_id(user_id)
        if not ratings:
            raise HTTPException(status_code=404, detail="No ratings found for this user")
        return UserRatingsListResponse(user_id=user_id, ratings=ratings)

    # Якщо передано обидва параметри — показуємо конкретну оцінку
    elif photo_id and user_id:
        rating = await rating_repo.get_rating(photo_id, user_id)
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found for this user on this photo")
        return PhotoRatingResponse(user_id=rating.user_id, rating=rating.rating)

    # Якщо не передано жодного параметра — повертаємо помилку
    raise HTTPException(status_code=400, detail="Either 'photo_id' or 'user_id' must be provided")


@photo_router.delete("/admin/{photo_id}",
                     status_code=status.HTTP_204_NO_CONTENT,
                     dependencies=FORMODER)
async def delete_any_photo(
                        photo_id: int,
                        db: AsyncSession = Depends(get_db),
                    ):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    await photo_repo.delete_photo(photo_id)
    return {"detail": "Photo deleted successfully"}
