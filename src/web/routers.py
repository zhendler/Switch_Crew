from tempfile import NamedTemporaryFile
from sqlalchemy.future import select
from fastapi import Depends, APIRouter, Request, Form, HTTPException, UploadFile, File, status
from config.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.pass_utils import verify_password
from src.auth.repos import UserRepository
from src.auth.utils import create_access_token, create_refresh_token, decode_access_token
from src.comments.repos import CommentsRepository
from src.models.models import User, Photo, photo_tags
from src.photos.repos import get_photo_by_user, get_photo, upload_photo_to_cloudinary, delete_photo
from src.tags.repos import TagRepository
from datetime import datetime
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy import insert
from src.utils.qr_code_helper import generate_qr_code
from src.web.repos import TagWebRepository
from typing import Optional
from sqlalchemy.orm import selectinload
from sqlalchemy import func

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def truncatechars(value: str, length: int):
    if len(value) > length:
        return value[:length] + "..."
    return value

templates.env.filters["truncatechars"] = truncatechars



@router.get("/")
async def read_root(
        request: Request,
        db: AsyncSession = Depends(get_db),
):

    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    users, photos, popular_tags, popular_users, recent_comments = await tag_web_repo.get_data_for_main_page()
    return templates.TemplateResponse("index.html", {"request": request, 'user': user,
                                                     'photos': photos, 'popular_users': popular_users,
                                                     'popular_tags': popular_tags, 'recent_comments': recent_comments})


@router.post("/create/",
                 summary="Create a new tag",
                 description="""This endpoint creates a new tag with the specified name.
    The tag name should be unique and must not exceed 50 characters.""")
async def create_tag(tag_name: str = Form(...), db: AsyncSession = Depends(get_db)):

    tag_repo = TagRepository(db)
    await tag_repo.create_tag(name=tag_name)
    return RedirectResponse("web/tags/", status_code=302)


@router.get('/tags/',
                summary="Get all tags",
                description="""This endpoint retrieves all tags stored in the database.
    It returns a list of all tag objects.""")
async def get_all_tags(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    error_message = request.query_params.get("error", "")
    if error_message == "no_permission":
        return HTMLResponse(content="<h3>You do not have permission to do it.</h3>", status_code=403)

    tag_repo = TagRepository(db)
    tags = await tag_repo.get_all_tags()
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    return templates.TemplateResponse("tags.html", {"request": request, "title": "Tags", "tags": tags, 'user': user})


@router.post('/tags/delete/',
                   summary="Delete a tag by name",
                   description="""This endpoint deletes a tag from the database by its name. 
    If the tag is not found, an error message is returned.""", operation_id="delete_tag", include_in_schema=False)
async def delete_tag_by_name(
        request: Request,
        tag_name: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    if user.role_id not in [1, 2]:
        return RedirectResponse(url="web/tags/?error=no_permission", status_code=302)

    tag_repo = TagRepository(db)
    await tag_repo.delete_tag_by_name(tag_name)

    return RedirectResponse("web/tags/", status_code=302)


@router.get('/tags/{tag_name}/photos/')
async def get_photos_by_tag(request: Request, tag_name: str, db: AsyncSession = Depends(get_db)):
    tag_repo = TagRepository(db)
    photos = await tag_repo.get_photos_by_tag(tag_name)
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    return templates.TemplateResponse("photos_by_tag.html",
                                          {"request": request, "title": tag_name.capitalize(), "photos": photos, 'user': user})


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get('/page/{username}')
async def page(request: Request, username: str, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user_page = await user_repo.get_user_by_username(username)
    date_obj = datetime.fromisoformat(str(user_page.created_at))
    date_of_registration = date_obj.strftime("%d-%m-%Y")
    photos = await get_photo_by_user(db, username)
    amount_of_photos = len(photos)

    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    return templates.TemplateResponse('page.html', {"request": request, 'user_page': user_page,
                                                    'user': user, 'photos': photos, 'Date_reg': date_of_registration,
                                                    "amount_of_photos": amount_of_photos})


@router.get('/photo/{photo_id}')
async def photo_page(request: Request, photo_id: int, db: AsyncSession = Depends(get_db)):
    photo = await get_photo(db, photo_id)
    photo.created_at = photo.created_at.isoformat()
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    return templates.TemplateResponse('photo_page.html', {"request": request, "photo": photo, 'user': user})


@router.get('/photos/upload_photo/')
async def upload_photo(request: Request, db: AsyncSession = Depends(get_db)):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    return templates.TemplateResponse('upload_photo.html', {"request": request, 'user': user})


@router.post("/upload_photo")
async def upload_photo(
        request: Request,
        description: str = Form(...),
        tags: Optional[str] = Form(None),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)

    if user is None:
        return RedirectResponse(url="web/tags/?error=no_permission", status_code=302)

    if tags:
        tags = [tag.strip() for tag in tags.split(',')]

    if len(tags) > 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 tags allowed")

    try:
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file.file.read())
            tmp_file_path = tmp_file.name
            cloudinary_url = await upload_photo_to_cloudinary(tmp_file_path)
    except Exception as e:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading to Cloudinary: {str(e)}")
    finally:
        tmp_file.close()

    qr_core_url = generate_qr_code(cloudinary_url)
    new_photo = Photo(
        url_link=cloudinary_url,
        description=description,
        owner_id=user.id,
        qr_core_url=qr_core_url
    )

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

    if os.path.exists(tmp_file_path):
        os.remove(tmp_file_path)

    return RedirectResponse(f"web/page/{user.username}", status_code=302)


@router.post("/photos/delete/{photo_id}")
async def delete_photo_by_id(request: Request, photo_id: int, db: AsyncSession = Depends(get_db)):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    photo = await get_photo(db, photo_id)
    username = photo.owner.username
    if photo:
        if user.id == photo.owner.id or user.role_id not in [1, 2]:
            await delete_photo(db, photo_id)
            return RedirectResponse(url=f"web/page/{username}", status_code=302)
        else:
            return RedirectResponse(url="web/tags/?error=no_permission", status_code=302)


@router.post("/comments/create/{photo_id}/", status_code=status.HTTP_201_CREATED)
async def create_comment_html(
        request: Request,
        photo_id: int,
        comment_content: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)
    if user:
        comment_repo = CommentsRepository(db)
        await comment_repo.create_comment(user.id, photo_id, comment_content)
        return RedirectResponse(url=f"web/photo/{photo_id}", status_code=302)
    else:
        return RedirectResponse(url="web/tags/?error=no_permission", status_code=302)


@router.post("/comments/delete/{comment_id}/")
async def delete_own_comment_html(
    request: Request,
    comment_id: int,
    db: AsyncSession = Depends(get_db)
):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)

    comment_repo = CommentsRepository(db)
    comment = await comment_repo.get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user.id or user.role not in [1, 2]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot delete this comment")
    await comment_repo.delete_comment(comment_id)

    return RedirectResponse(url=f"web/photo/{comment.photo_id}", status_code=302)


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

    response = RedirectResponse(url="/web", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/web", status_code=302)
    response.delete_cookie(key="access_token", httponly=True)
    response.delete_cookie(key="refresh_token", httponly=True)
    return response


@router.get('/photos/photos/')
async def get_photos(request: Request, page: int = 1, db: AsyncSession = Depends(get_db)):
    tag_web_repo = TagWebRepository(db)
    user = await tag_web_repo.get_current_user_cookies(request)

    photos_per_page = 20
    offset = (page - 1) * photos_per_page

    photos_query = (
        select(Photo)
        .options(selectinload(Photo.owner), selectinload(Photo.tags), selectinload(Photo.comments))
        .order_by(Photo.created_at.desc())
        .offset(offset)
        .limit(photos_per_page)
    )
    result = await db.execute(photos_query)
    photos = result.scalars().all()

    total_photos_query = select(func.count(Photo.id))
    total_photos_result = await db.execute(total_photos_query)
    total_photos = total_photos_result.scalar()

    total_pages = (total_photos + photos_per_page - 1) // photos_per_page
    return templates.TemplateResponse(
        "all_photos.html",
        {
            "title": 'Photos',
            "request": request,
            "photos": photos,
            "current_page": page,
            "total_pages": total_pages,
            "user": user
        },
    )

