from fastapi import APIRouter, UploadFile, HTTPException, status, Depends, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader

from config.db import get_db
from config.general import settings
from src.models.models import User, Role, Photo
from src.user_profile.schemas import (
    UserProfileUpdate, 
    UserProfileResponse, 
    AdminUserProfileResponse, 
    UserAvatarResponse
)
from src.user_profile.repos import UserProfileRepository
from src.auth.repos import UserRepository, RoleRepository
from src.auth.utils import FORADMIN, ACTIVATE, get_current_user
from src.auth.schemas import RoleEnum


router = APIRouter()


@router.put("/update-profile", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def update_own_profile(
    user_update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_repo = UserProfileRepository(db)
    updated_user = await user_repo.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    query = select(func.count(Photo.id)).where(Photo.owner_id == current_user.id)
    result = await db.execute(query)
    uploaded_photos_count = result.scalar()
    return UserProfileResponse(
        id=updated_user.id,
        username=updated_user.username,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        email=updated_user.email,
        birth_date=updated_user.birth_date,
        country=updated_user.country,
        created_at=updated_user.created_at,
        uploaded_photos=uploaded_photos_count,
    )


@router.patch('/update_avatar', response_model=UserAvatarResponse, status_code=status.HTTP_200_OK)
async def update_own_avatar(
    file: UploadFile = File(), 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    try:
        r = cloudinary.uploader.upload(
            file.file, 
            public_id=f'avatars/{current_user.username}',
            overwrite=True,
        )
        src_url = cloudinary.CloudinaryImage(f'avatars/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading avatar: {str(e)}"
        )
    user_repo = UserRepository(db)
    user = await user_repo.update_avatar(current_user.email, src_url)
    return user


@router.get("/my_profile", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_own_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserProfileRepository(db)
    user= await user_repo.get_user(current_user.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    query = select(func.count(Photo.id)).where(Photo.owner_id == current_user.id)
    result = await db.execute(query)
    uploaded_photos_count = result.scalar()
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        birth_date=user.birth_date,
        country=user.country,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        uploaded_photos=uploaded_photos_count
    )


@router.get(
    "/profile/{username}", 
    response_model=UserProfileResponse, 
    dependencies=ACTIVATE,
    status_code=status.HTTP_200_OK
)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_repo = UserProfileRepository(db)
    user = await user_repo.get_user(username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with username '{username}' not found."
        )
    query = select(func.count(Photo.id)).where(Photo.owner_id == user.id)
    result = await db.execute(query)
    uploaded_photos_count = result.scalar()

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        birth_date=user.birth_date,
        country=user.country,
        created_at=user.created_at,
        uploaded_photos=uploaded_photos_count
    )


@router.get(
    "/admin/profile/{username}", 
    response_model=AdminUserProfileResponse, 
    dependencies=FORADMIN, 
    status_code=status.HTTP_200_OK
)
async def get_user_profile_for_admin(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_repo = UserProfileRepository(db)
    user = await user_repo.get_user(username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with username '{username}' not found."
        )
    q_photo = select(func.count(Photo.id)).where(Photo.owner_id == user.id)
    r_photo = await db.execute(q_photo)
    uploaded_photos_count = r_photo.scalar()

    q_role_name = select(Role.name).where(Role.id == user.role_id)
    r_role_name = await db.execute(q_role_name)
    user_role_name = r_role_name.scalar()
    return AdminUserProfileResponse(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        birth_date=user.birth_date,
        country=user.country,
        created_at=user.created_at,
        uploaded_photos=uploaded_photos_count,
        role_name=user_role_name,
        is_active=user.is_active,
        is_banned=user.is_banned
    )


@router.put("/admin/{user_id}/role", dependencies=FORADMIN, status_code=status.HTTP_200_OK)
async def change_user_role(user_id: int, role: RoleEnum, db: AsyncSession = Depends(get_db)):
    if role not in [RoleEnum.USER, RoleEnum.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin can only assign 'USER' or 'MODERATOR' roles"
        )
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    role_repo = RoleRepository(db)
    role_obj = await role_repo.get_role_by_name(role)
    if not role_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    user.role = role_obj
    await db.commit()
    return {"msg": "User role updated successfully"}


@router.put("/admin/ban_user/{username}", dependencies=FORADMIN, status_code=status.HTTP_200_OK)
async def ban_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot ban yourself."
        )
    user_repo = UserProfileRepository(db)
    user = await user_repo.ban_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found."
        )
    return {"detail": f"User '{username}' has been banned."}


@router.put("/admin/unban_user/{username}", dependencies=FORADMIN, status_code=status.HTTP_200_OK)
async def unban_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot ban yourself."
        )
    user_repo = UserProfileRepository(db)
    user = await user_repo.unban_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found."
        )
    return {"detail": f"User '{username}' has been unbanned."}