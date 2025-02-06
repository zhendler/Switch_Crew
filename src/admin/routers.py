from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.admin.repos import AdminRepository
from src.admin.schemas import UserForAdmin, UserNameForAdmin, UserFullInformationAdmin
from src.auth.repos import UserRepository
from src.auth.utils import get_current_user_cookies
from src.photos.repos import PhotoRepository
from src.utils.front_end_utils import get_response_format, templates

router = APIRouter()

@router.get("/userinfo")
async def a_users_info(request: Request, db: AsyncSession = Depends(get_db)):

    return templates.TemplateResponse("/admin/test.html", {"request": request})



@router.get("/users", response_model=list[UserForAdmin])
async def a_get_all_users(
        request: Request,
        db: AsyncSession = Depends(get_db),
        response_format: str = Depends(get_response_format),
):

    admin_repository = AdminRepository(db)
    users = await admin_repository.get_all_users()
    return users


@router.get("/usernames_list", response_model=list[UserNameForAdmin])
async def a_get_usernames_list(
        request: Request,
        db: AsyncSession = Depends(get_db),
        ):

    admin_repository = AdminRepository(db)
    usernames = await admin_repository.get_usernames_list()

    return usernames



@router.get("/{user_id}", response_model=UserFullInformationAdmin)
async def a_get_user_by_id(
        user_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        response_format: str = Depends(get_response_format),
):
    admin_repository = AdminRepository(db)
    user = await admin_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="U21212ser not found")
    return user



router.get("/username/{username}")
async def page(request: Request, username: str, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user_page = await user_repo.get_user_by_username(username)
    date_obj = datetime.fromisoformat(str(user_page.created_at))
    date_of_registration = date_obj.strftime("%d-%m-%Y")
    photo_repo = PhotoRepository(db)
    photos = await photo_repo.get_users_all_photos(user_page)
    amount_of_photos = len(photos)

    user = await get_current_user_cookies(request, db)
    return templates.TemplateResponse(
        "/user/page.html",
        {
            "request": request,
            "user_page": user_page,
            "user": user,
            "photos": photos,
            "Date_reg": date_of_registration,
            "amount_of_photos": amount_of_photos,
        },
    )



# @router.get('/search/')
# async def search(
#     request: Request,
#     query: str,
#     db: AsyncSession = Depends(get_db),
# ):
#     user_repo = UserProfileRepository(db)
#     tag_repo = TagRepository(db)
#
#     tags = await tag_repo.search_tags(query)
#     searched_users = await user_repo.search_users(query)
#
#     user = await get_current_user_cookies(request, db)
#     return templates.TemplateResponse(
#             "/main/search.html",
#             {"request": request,
#             "user": user,
#             'query': query,
#             'searched_users': searched_users,
#              'tags': tags}
#         )
