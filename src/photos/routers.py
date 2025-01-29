from typing import List, Union, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
    Query,
    Path, Form,
)
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from cloudinary.utils import cloudinary_url
from starlette.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from config.db import get_db
from src.auth.utils import get_current_user, FORALL, FORMODER, get_current_user_cookies
from src.models.models import User
from src.photos.repos import PhotoRepository, PhotoRatingRepository
from src.photos.schemas import (
    PhotoResponse,
    PhotoUpdate,
    UrlPhotoResponse,
    PhotoRatingsListResponse,
    UserRatingsListResponse,
    PhotoRatingResponse,
    AverageRatingResponse,
)
from src.utils.cloudinary_helper import (
    upload_photo_to_cloudinary,
    get_cloudinary_image_id,
)
from src.utils.front_end_utils import templates, get_response_format
from src.utils.qr_code_helper import generate_qr_code


photo_router = APIRouter()
mainrouter = APIRouter()

templates = Jinja2Templates(directory="templates")


def truncatechars(value: str = "1", length: int = 35):
    if len(value) > length:
        return value[:length] + "..."
    return value

templates.env.filters["truncatechars"] = truncatechars


@mainrouter.get("/")
async def read_root(
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    user = await get_current_user_cookies(request, db)
    photo_repo = PhotoRepository(db)
    popular_users, photos, popular_tags, recent_comments = (
        await photo_repo.get_data_for_main_page()
    )
    return templates.TemplateResponse(
        "/main/index.html",
        {
            "request": request,
            "user": user,
            "photos": photos,
            "popular_users": popular_users,
            "popular_tags": popular_tags,
            "recent_comments": recent_comments,
        },
    )

@photo_router.get("/upload_photo/")
async def upload_photo(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_cookies(request, db)
    return templates.TemplateResponse(
        "/photos/upload_photo.html", {"request": request, "user": user}
    )

@photo_router.post(
    "/create/",
    response_model= Union[PhotoResponse, str],
    status_code=status.HTTP_201_CREATED,
    )
async def create_photo(
    request: Request,
    description: str = Form(...),
    tags: Optional[str] = Form(None), # TODO: виправити ТЕГИ з рядка в список, так щоб форма приймала список тегів
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    response_format: str = Depends(get_response_format)
):
    cloudinary_url = await upload_photo_to_cloudinary(file)
    user = await get_current_user_cookies(request, db)

    photo_repo = PhotoRepository(db)
    new_photo = await photo_repo.create_photo(cloudinary_url, description, user, tags)
    if response_format == "json":
        return new_photo
    else:
        return RedirectResponse(f"/photos/{new_photo.id}", status_code=302)


    Returns:
        list[PhotoResponse]: A list of the user's photos.

    Raises:
        HTTPException: If no photos are found for the user.
    """
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_users_all_photos(user)
    if not photos:
        raise HTTPException(status_code=404, detail="Photos not found")
    return photos


@photo_router.get(
    "/all_photos",
    response_model=list[PhotoResponse]
)
async def all_photos(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    response_format: str = Depends(get_response_format)
):
    user = await get_current_user_cookies(request, db)
    photo_repo = PhotoRepository(db)
    photos, total_pages = await photo_repo.get_all_photos(page)
    if not photos:
        raise HTTPException(status_code=404, detail="Photos not found")
    if response_format == "json":
        return photos
    else:
        return templates.TemplateResponse(
        "/photos/all_photos.html",
        {
            "title": "Photos",
            "request": request,
            "photos": photos,
            "current_page": page,
            "total_pages": total_pages,
            "user": user,
        },
    )



@photo_router.get(
    "/get_url/{photo_id}", response_model=UrlPhotoResponse, dependencies=FORALL
)
async def get_photo_url(
    photo_id: int = Path(..., description="ID of the photo"),
    db: AsyncSession = Depends(get_db),
) -> UrlPhotoResponse:
    """
    Retrieve the URL of a photo by its ID.

    This endpoint fetches the URL of a specific photo identified by its ID.

    Args:
        photo_id (int): The ID of the photo.
        db (AsyncSession): The database session.

    Returns:
        UrlPhotoResponse: The photo's URL.

    Raises:
        HTTPException: If the photo does not exist.
    """
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@photo_router.get("/{photo_id}")
async def photo_page(
        request: Request,
        photo_id: int,
        db: AsyncSession = Depends(get_db),
        response_format: str = Depends(get_response_format)
):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with id {photo_id} not found",
        )

    photo.created_at = photo.created_at.isoformat()

    user = await get_current_user_cookies(request, db)
    if response_format == "json":
        return photo
    else:
        return templates.TemplateResponse(
        "/photos/photo_page.html", {"request": request, "photo": photo, "user": user}
    )

# @photo_router.get("/{photo_id}", response_model=PhotoResponse, dependencies=FORALL)
# async def get_photo_by_id(
#     photo_id: int = Path(..., description="ID of the photo"),
#     db: AsyncSession = Depends(get_db),
# ) -> PhotoResponse:
#     """
#     Retrieve details of a photo by its ID.
#
#     This endpoint fetches details of a specific photo identified by its ID.
#
#     Args:
#         photo_id (int): The ID of the photo.
#         db (AsyncSession): The database session.
#
#     Returns:
#         PhotoResponse: The photo's details.
#
#     Raises:
#         HTTPException: If the photo does not exist.
#     """
#     photo_repo = PhotoRepository(db)
#     photo = await photo_repo.get_photo_by_id(photo_id)
#
#     if photo is None:
#         raise HTTPException(status_code=404, detail="Photo not found")
#     return photo


@photo_router.put(
    "/update/{photo_id}", response_model=PhotoResponse, dependencies=FORALL
)
async def update_photo_description(
    photo_id: int,
    photo: PhotoUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the description of a photo.

    This endpoint allows the authenticated user to update the description of a photo they own.

    Args:
        photo_id (int): The ID of the photo.
        photo (PhotoUpdate): The new description for the photo.
        user (User): The authenticated user making the request.
        db (AsyncSession): The database session.

    Returns:
        PhotoResponse: The updated photo details.
    """
    photo_repo = PhotoRepository(db)
    update_photo = await photo_repo.update_photo_description(
        photo_id, photo.description, user.id
    )
    return update_photo


@photo_router.post("/delete/{photo_id}")
async def delete_photo_by_id(
    request: Request, photo_id: int, db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_cookies(request, db)

    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)
    username = photo.owner.username
    if photo:
        if user.id == photo.owner.id or user.role_id not in [1, 2]:
            await photo_repo.delete_photo(photo_id)
            return RedirectResponse(url=f"/page/{username}", status_code=302)
        else:
            return RedirectResponse(
                url="/tags/?error=no_permission", status_code=302
            )

@photo_router.delete(
    "/{photo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=FORALL
)
async def delete_own_photo(
    photo_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a photo uploaded by the current user.

    This endpoint allows the authenticated user to delete one of their own photos.

    Args:
        photo_id (int): The ID of the photo to delete.
        user (User): The authenticated user making the request.
        db (AsyncSession): The database session.

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If the photo does not exist or does not belong to the user.
    """
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    if photo.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="You can delete only your own photos"
        )

    await photo_repo.delete_photo(photo_id)
    return {"detail": "Photo deleted successfully"}


@photo_router.get(
    "/{photo_id}/transform",
    dependencies=FORALL,
)
async def transform_photo(
    photo_id: int,
    width: int = Query(None, description="Width of the transformed photo"),
    height: int = Query(None, description="Height of the transformed photo"),
    crop: str = Query(None, description="Crop mode (e.g., 'fill', 'fit')"),
    effect: str = Query(
        None, description="Effect to apply (e.g., 'sepia', 'grayscale')"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Transform a photo by applying specified parameters (e.g., resizing, cropping, effects).

    Args:
        photo_id (int): The ID of the photo to transform.
        width (int, optional): The width of the transformed photo.
        height (int, optional): The height of the transformed photo.
        crop (str, optional): The crop mode to apply.
        effect (str, optional): The effect to apply to the photo.
        db (AsyncSession): The database session.

    Returns:
        dict: A dictionary containing the original URL, transformed URL, and QR code URL.

    Raises:
        HTTPException: If the photo does not exist.
        ValueError: If the Cloudinary URL is invalid.
    """
    # Retrieve the photo from the database
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

    return {
        "original_url": photo.url_link,
        "transformed_url": transformed_url,
        "qr_code_url": qr_code_data,
    }


@photo_router.post("/rate/{photo_id}", dependencies=FORALL)
async def rate_photo(
    photo_id: int = Path(..., description="ID of the photo"),
    rating: int = Query(..., ge=1, le=5, description="Rating between 1 and 5"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rate a photo.

    This endpoint allows an authenticated user to rate a photo. Users cannot rate their own photos.

    Args:
        photo_id (int): The ID of the photo to rate.
        rating (int): The rating to assign (1-5).
        user (User): The authenticated user making the request.
        db (AsyncSession): The database session.

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If the photo does not exist or if the user attempts to rate their own photo.
    """
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if photo.owner_id == user.id:
        raise HTTPException(status_code=403, detail="You cannot rate your own photo.")

    rating_repo = PhotoRatingRepository(db)
    await rating_repo.add_and_update_rating(photo_id, user.id, rating)

    return {"detail": "Rating added successfully."}


@photo_router.get(
    "/rating/{photo_id}", response_model=AverageRatingResponse, dependencies=FORALL
)
async def get_current_photo_ratings(
    photo_id: int = Path(..., description="ID of the photo"),
    db: AsyncSession = Depends(get_db),
) -> AverageRatingResponse:
    """
    Retrieve the average rating of a photo.

    This endpoint fetches the average rating of a specific photo.

    Args:
        photo_id (int): The ID of the photo.
        db (AsyncSession): The database session.

    Returns:
        AverageRatingResponse: The average rating of the photo.

    Raises:
        HTTPException: If the photo has not been rated yet.
    """

    rating_repo = PhotoRatingRepository(db)
    rating = await rating_repo.get_average_rating(photo_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Not rated yet")

    return AverageRatingResponse(rating=rating)


@photo_router.delete("/admin/del_rate", dependencies=FORMODER)
async def delete_photo_rating(
    photo_id: int = Query(
        ..., description="ID of the photo whose rating needs to be deleted"
    ),
    user_id: int = Query(
        ..., description="ID of the user whose rating needs to be deleted"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user's rating for a photo.

    This endpoint allows a moderator to delete a specific user's rating for a photo.

    Args:
        photo_id (int): The ID of the photo.
        user_id (int): The ID of the user whose rating will be deleted.
        db (AsyncSession): The database session.

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If the photo or rating does not exist.
    """
    # Retrieve the photo by ID
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    rating_repo = PhotoRatingRepository(db)
    rating = await rating_repo.get_rating(photo_id, user_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    # Delete the rating
    await rating_repo.delete_rating(photo_id, user_id)

    # Update the average rating
    await rating_repo.update_average_rating(photo_id)

    return {"detail": "Rating deleted successfully."}


@photo_router.get(
    "/admin/rate",
    dependencies=FORMODER,
    response_model=Union[
        PhotoRatingsListResponse, UserRatingsListResponse, PhotoRatingResponse
    ],
)
async def get_ratings_by_user_or_photo(
    photo_id: int = Query(None, description="ID of the photo to fetch ratings for"),
    user_id: int = Query(None, description="ID of the user to fetch ratings for"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve ratings by photo or user.

    This endpoint allows moderators to fetch ratings based on photo ID, user ID, or both.

    Args:
        photo_id (int, optional): The ID of the photo to fetch ratings for.
        user_id (int, optional): The ID of the user to fetch ratings for.
        db (AsyncSession): The database session.

    Returns:
        Union[PhotoRatingsListResponse, UserRatingsListResponse, PhotoRatingResponse]:
            A response containing the requested ratings.

    Raises:
        HTTPException: If no parameters are provided or no ratings are found.
    """
    rating_repo = PhotoRatingRepository(db)

    # If only photo_id is passed - show all ratings for the photo
    if photo_id and not user_id:
        ratings = await rating_repo.get_ratings_by_photo_id(photo_id)
        if not ratings:
            raise HTTPException(
                status_code=404, detail="No ratings found for this photo"
            )
        return PhotoRatingsListResponse(photo_id=photo_id, ratings=ratings)

    # If only user_id is passed - show all ratings of this user
    elif user_id and not photo_id:
        ratings = await rating_repo.get_ratings_by_user_id(user_id)
        if not ratings:
            raise HTTPException(
                status_code=404, detail="No ratings found for this user"
            )
        return UserRatingsListResponse(user_id=user_id, ratings=ratings)

    # If both parameters are passed, we show a specific score
    elif photo_id and user_id:
        rating = await rating_repo.get_rating(photo_id, user_id)
        if not rating:
            raise HTTPException(
                status_code=404, detail="Rating not found for this user on this photo"
            )
        return PhotoRatingResponse(user_id=rating.user_id, rating=rating.rating)

    # If no parameters are passed, return an error
    raise HTTPException(
        status_code=400, detail="Either 'photo_id' or 'user_id' must be provided"
    )


@photo_router.delete(
    "/admin/{photo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=FORMODER
)
async def delete_any_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete any photo by its ID (admin-only operation).

    This endpoint allows a moderator to delete any photo by its unique ID. This is intended
    for administrative purposes only and requires elevated permissions.
    """
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.get_photo_by_id(photo_id)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    await photo_repo.delete_photo(photo_id)
    return {"detail": "Photo deleted successfully"}
