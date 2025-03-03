from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import current_user
from starlette import status

from config.db import get_db
from src.admin.repos import AdminRepository
from src.admin.schemas import UserForAdmin, UserNameForAdmin, UserFullInformationAdmin, UserCommentsForAdmin, RoleEnum
from src.auth.repos import UserRepository
from src.auth.utils import get_current_user_cookies, FORMODER
from src.photos.repos import PhotoRepository
from src.utils.front_end_utils import get_response_format, templates

router = APIRouter()

@router.get("/userinfo", dependencies= FORMODER)
async def a_users_info(request: Request,
                       db: AsyncSession = Depends(get_db)):
    user = await get_current_user_cookies(request, db)

    return templates.TemplateResponse("/admin/a_users.html", {"request": request, "user": user} )



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
        db: AsyncSession = Depends(get_db),
        response_format: str = Depends(get_response_format),
):
    admin_repository = AdminRepository(db)
    user = await admin_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="U21212ser not found")
    return user

@router.get("/users_comments/{user_id}", response_model=list[UserCommentsForAdmin])
async def get_user_comments(
        user_id: int,
    db: AsyncSession = Depends(get_db)
):

    admin_repo = AdminRepository(db)
    comments = await admin_repo.get_all_users_comments(user_id)
    return comments


@router.put("/ban_unban_user/{user_id}", status_code=status.HTTP_200_OK)
async def ban_unban_user(
        request: Request,
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    curr_user = await get_current_user_cookies(request, db)

    if curr_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "You can't ban/unban yourself", "error_code": 403}
        )
    admin_repo = AdminRepository(db)
    user = await admin_repo.ban_unban(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "error_code": 404}
        )
    return {
        "message": f"User {user.username} {'banned' if user.is_banned else 'unbanned'} successfully",
        "is_banned": user.is_banned
    }


@router.put("/change_role/{user_id}/", status_code=status.HTTP_200_OK)
async def change_user_role(
        request: Request,
        user_id: int,
        role: RoleEnum,
        db: AsyncSession = Depends(get_db)
):
    curr_user = await get_current_user_cookies(request, db)

    if curr_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "You can't change your own role", "error_code": 403}
        )
    if role not in [RoleEnum.USER, RoleEnum.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Admin can only assign 'USER' or 'MODERATOR' roles", "error_code": 400}
        )
    admin_repo = AdminRepository(db)
    user = await admin_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "error_code": 404}
        )
    role_obj = await admin_repo.get_role_by_name(role)
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Role not found", "error_code": 404}
        )
    user.role = role_obj
    await db.commit()
    return {"message": "Role changed successfully"}





















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
