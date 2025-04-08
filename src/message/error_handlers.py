from fastapi import HTTPException, status

from src.models.models import User, Message


def check_exists(obj, detail: str) -> None:
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def check_owner(current_user: User, owner_id: int, detail: str) -> None:
    if current_user.id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def prevent_self_action(current_user: User, obj_id: int, detail: str) -> None:
    if current_user.id == obj_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
