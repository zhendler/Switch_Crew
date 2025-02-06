from typing import List
from datetime import datetime

from fastapi import (
    Depends,
    APIRouter,
    Request,
    Form,
    HTTPException,
    UploadFile,
    File,
    status,
    BackgroundTasks
)
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.mail_utils import send_verification_grid
from src.auth.routers import env
from src.auth.schemas import UserResponse, UserCreate
from src.auth.pass_utils import verify_password
from src.auth.repos import UserRepository
from src.auth.utils import create_access_token, create_refresh_token, create_verification_token, \
    get_current_user_cookies
from src.comments.repos import CommentsRepository
from src.models.models import Photo
from src.photos.repos import PhotoRepository
from src.tags.repos import TagRepository
from config.db import get_db

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def truncatechars(value: str = "1", length: int = 35):
    if len(value) > length:
        return value[:length] + "..."
    return value


templates.env.filters["truncatechars"] = truncatechars


@router.post(
    "/tags/delete/",
    summary="Delete a tag by name",
    description="""This endpoint deletes a tag from the database by its name. 
    If the tag is not found, an error message is returned.""",
    operation_id="delete_tag",
    include_in_schema=False,
)
async def delete_tag_by_name(
    request: Request, tag_name: str = Form(...), db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_cookies(request, db)
    if user.role_id not in [1, 2]:
        return RedirectResponse(url="/tags/?error=no_permission", status_code=302)

    tag_repo = TagRepository(db)
    await tag_repo.delete_tag_by_name(tag_name)

    return RedirectResponse("/tags/", status_code=302)


@router.get("/tag/{tag_name}/photos/")
async def get_photos_by_tag(
    request: Request, tag_name: str, db: AsyncSession = Depends(get_db)
):
    tag_repo = TagRepository(db)

    photos = await tag_repo.get_photos_by_tag(tag_name)
    user = await get_current_user_cookies(request, db)

    if isinstance(photos, List):
        return templates.TemplateResponse(
            "/photos/photos_by_tag.html",
            {
                "request": request,
                "title": tag_name.capitalize(),
                "photos": photos,
                "user": user,
            },
        )

    else:
        return templates.TemplateResponse(
            "/photos/photos_by_tag.html",
            {
                "request": request,
                "title": tag_name.capitalize(),
                "user": user,
            },
        )


@router.get("/page/{username}")
async def page(request: Request,
               username: str,
               db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    photo_repo = PhotoRepository(db)

    user_page = await user_repo.get_user_by_username(username)
    user = await get_current_user_cookies(request, db)

    date_obj = datetime.fromisoformat(str(user_page.created_at))
    date_of_registration = date_obj.strftime("%Y-%m-%d")

    photos = await photo_repo.get_users_all_photos(user_page)
    amount_of_photos = len(photos)

    detail = request.query_params.get("detail")

    return templates.TemplateResponse(
        "/user/page.html",
        {
            "request": request,
            "user_page": user_page,
            "user": user,
            "photos": photos,
            "Date_reg": date_of_registration,
            "amount_of_photos": amount_of_photos,
            "detail": detail,
        },
    )


# @router.get("/photo/{photo_id}")
# async def photo_page(
#     request: Request, photo_id: int, db: AsyncSession = Depends(get_db)
# ):
#     photo_repo = PhotoRepository(db)
#     reaction_repo = ReactionRepository(db)
#
#     user = await get_current_user_cookies(request, db)
#     photo = await photo_repo.get_photo_by_id(photo_id)
#     if user:
#         reaction_active = await reaction_repo.get_reaction_by_user_and_photo(photo_id, user.id)
#     else:
#         reaction_active = None
#
#     if not photo:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Photo with id {photo_id} not found",
#         )
#
#     photo.created_at = photo.created_at.isoformat()
#     reaction_counts = await reaction_repo.get_reaction_counts(photo_id)
#
#     return templates.TemplateResponse(
#         "/photos/photo_page.html", {"request": request,
#                                     "photo": photo,
#                                     "user": user,
#                                     "reaction_active": reaction_active,
#                                     "reaction_counts": reaction_counts}
#     )


@router.post("/photos/delete/{photo_id}")
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


@router.post("/comments/create/{photo_id}/", status_code=status.HTTP_201_CREATED)
async def create_comment_html(
    request: Request,
    photo_id: int,
    comment_content: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user_cookies(request, db)
    if user:
        comment_repo = CommentsRepository(db)
        comment = await comment_repo.create_comment(user.id, photo_id, comment_content)
        return JSONResponse(
            content={
                "id": comment.id,
                "content": comment_content,
                "user": {
                    "username": user.username,
                    "avatar_url": user.avatar_url,
                },
                "permissions": {
                    "can_edit": True,
                    "can_delete": True,
                },
            },
            status_code=201,
        )
    else:
        return JSONResponse(
            content={"error": "No permission"},
            status_code=403,
        )


@router.post("/comment/delete/{comment_id}/")
async def delete_comment_html(
        request: Request, comment_id: int, db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_cookies(request, db)

    comment_repo = CommentsRepository(db)
    comment = await comment_repo.get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    if (comment.user_id is user.id) or (user.role_id in [1, 2]) or (comment.photo.owner_id is user.id):
        await comment_repo.delete_comment(comment_id)
        return JSONResponse(content={"message": "Комментарий удален"}, status_code=200)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete this comment",
        )


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("/authentication/login.html", {"request": request})


@router.post("/login/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token", httponly=True)
    response.delete_cookie(key="refresh_token", httponly=True)
    return response


@router.get(
    "/register_page",
    status_code=status.HTTP_200_OK,
)
async def register_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_cookies(request, db)
    if user is None:
        return templates.TemplateResponse(
            "/authentication/register.html", {"request": request, "user": user}
        )
    else:
        return templates.TemplateResponse(
            "/main/index.html", {"request": request, "user": user}
        )


@router.post(
    "/registration",
    status_code=status.HTTP_201_CREATED,
)
async def registration(
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    avatar: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    Args:
        background_tasks (BackgroundTasks): Background task manager for sending verification email.
        username (str): The username of the new user.
        email (str): The email of the new user.
        password (str): The password of the new user.
        avatar (UploadFile, optional): The avatar file for the new user.
        db (AsyncSession): Database session dependency.

    Returns:
        UserResponse: Details of the newly created user along with a verification message.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already register"
        )
    user_create = UserCreate(
        username=username, email=email, password=password, avatar=avatar
    )
    user = await user_repo.create_user(user_create)
    if avatar:
        avatar_url = await user_repo.upload_to_cloudinary(avatar)
        await user_repo.update_avatar(user.email, avatar_url)
    verification_token = create_verification_token(user.email)
    verification_link = f"https://localhost:8000/auth/verify-email?token={verification_token}"
    template = env.get_template("email.html")
    email_body = template.render(verification_link=verification_link)
    background_tasks.add_task(send_verification_grid, user.email, email_body)

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return response


@router.post('/comment/edit/{comment_id}/')
async def edit_comment(request: Request, comment_id, db: AsyncSession = Depends(get_db)):
    com_repo = CommentsRepository(db)

    comment = await com_repo.get_comment_by_id(int(comment_id))
    user = await get_current_user_cookies(request, db)

    if comment.user.id == user.id or user.role_id in [1, 2]:
        form_data = await request.form()
        comment_content = form_data.get('comment_content')

        if comment_content:
            comment.content = comment_content
            await db.commit()
            return JSONResponse(content={"message": "Comment updated"}, status_code=200)

        return 'Invalid content', 400
    return 'Forbidden', 403

@router.post("/photos/edit-description/{photo_id}/")
async def edit_photo_description(request: Request, photo_id: int, description: str = Form(...), db: AsyncSession = Depends(get_db)):
    photo = await db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    user = await get_current_user_cookies(request, db)

    if photo.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this photo")

    photo.description = description
    await db.commit()

    return {"message": "Description updated successfully"}

