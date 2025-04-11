from fastapi import HTTPException, status

from src.models.models import User


def check_exists(obj, detail: str) -> None:
    """Check if an object exists, otherwise raise a 404 Not Found error.
    Args:
        obj: The object to check for existence.
        detail: The error detail message to include in the HTTPException if the object doesn't exist.
    Raises:
        HTTPException: 404 Not Found if the object doesn't exist.
    """
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def check_owner(current_user: User, owner_id: int, detail: str) -> None:
    """Check if the current user is the owner, otherwise raise a 403 Forbidden error.
    Args:
        current_user: The authenticated user making the request.
        owner_id: The ID of the owner to compare against.
        detail: The error detail message to include in the HTTPException if the user is not the owner.
    Raises:
        HTTPException: 403 Forbidden if the current user is not the owner.
    """
    if current_user.id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def prevent_self_action(current_user: User, obj_id: int, detail: str) -> None:
    """Prevent a user from performing an action on themselves, otherwise raise a 400 Bad Request error.
    Args:
        current_user: The authenticated user making the request.
        obj_id: The ID to compare against the user's ID.
        detail: The error detail message to include in the HTTPException if the IDs match.
    Raises:
        HTTPException: 400 Bad Request if the current user's ID matches the object ID.
    """
    if current_user.id == obj_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
