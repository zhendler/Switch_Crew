from fastapi import APIRouter, Depends, status, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from config.db import get_db
from src.auth.utils import get_current_user, FORALL, FORMODER, get_current_user_cookies
from src.comments.repos import CommentsRepository
from src.comments.schemas import CommentResponse, CommentCreate
from src.models.models import User
from src.utils.front_end_utils import get_response_format

router = APIRouter()


# @router.post(
#     "/",
#     response_model=CommentResponse,
#     dependencies=FORALL,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_comment(
#     comment: CommentCreate,
#     user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Creates a new comment for a photo.
#
#     :param comment: The data for the comment to be created.
#     :param user: The current authenticated user (injected via dependency).
#     :param db: The database session (injected via dependency).
#     :return: The created comment as a response model.
#     """
#     comment_repo = CommentsRepository(db)
#     return await comment_repo.create_comment(user.id, comment.photo_id, comment.content)

@router.post("/create/{photo_id}/", status_code=status.HTTP_201_CREATED)
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


@router.get("/user/", response_model=list[CommentResponse], dependencies=FORALL)
async def get_user_comments(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all comments created by the current authenticated user.

    :param user: The current authenticated user (injected via dependency).
    :param db: The database session (injected via dependency).
    :return: A list of comments made by the user.
    """
    comment_repo = CommentsRepository(db)
    return await comment_repo.get_comments_by_user(user.id)


@router.get(
    "/photo/{photo_id}/", response_model=list[CommentResponse], dependencies=FORALL
)
async def get_photo_comments(
    photo_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    responese_format: str = Depends(get_response_format),
):
    """
    Retrieves all comments associated with a specific photo.

    :param photo_id: The ID of the photo.
    :param user: The current authenticated user (injected via dependency).
    :param db: The database session (injected via dependency).
    :return: A list of comments for the specified photo.
    """
    comment_repo = CommentsRepository(db)
    return await comment_repo.get_comments_by_photo(photo_id)


@router.get(
    "/user/{user_id}/comments",
    response_model=list[CommentResponse],
    dependencies=FORMODER,
)
async def get_comments_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves all comments made by a specific user.

    :param user_id: The ID of the user whose comments are to be retrieved.
    :param db: The database session (injected via dependency).
    :return: A list of comments made by the specified user.
    """
    comment_repo = CommentsRepository(db)
    return await comment_repo.get_comments_by_user(user_id)


# @router.put("/{comment_id}/", response_model=CommentResponse, dependencies=FORALL)
# async def update_comment(
#     comment_id: int,
#     content: str,
#     user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Updates an existing comment created by the current user.
#
#     :param comment_id: The ID of the comment to be updated.
#     :param content: The updated content for the comment.
#     :param user: The current authenticated user (injected via dependency).
#     :param db: The database session (injected via dependency).
#     :return: The updated comment as a response model.
#     """
#     comment_repo = CommentsRepository(db)
#     return await comment_repo.update_comment(
#         comment_id=comment_id, user_id=user.id, content=content
#     )

@router.post('/edit/{comment_id}/')
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


# @router.delete(
#     "/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=FORALL
# )
# async def delete_own_comment(
#     comment_id: int,
#     user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Deletes a comment created by the current user.
#
#     :param comment_id: The ID of the comment to be deleted.
#     :param user: The current authenticated user (injected via dependency).
#     :param db: The database session (injected via dependency).
#     :raises HTTPException: If the comment does not exist or the user lacks permission.
#     """
#     comment_repo = CommentsRepository(db)
#     comment = await comment_repo.get_comment_by_id(comment_id)
#     if not comment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
#         )
#     if comment.user_id != user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You cannot delete this comment",
#         )
#     await comment_repo.delete_comment(comment_id)


@router.post("/delete/{comment_id}/")
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


# @router.delete(
#     "/admin/{comment_id}/",
#     status_code=status.HTTP_204_NO_CONTENT,
#     dependencies=FORMODER,
# )
# async def delete_any_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
#     """
#     Deletes a comment by its ID. Accessible only to moderators and administrators.
#
#     :param comment_id: The ID of the comment to be deleted.
#     :param db: The database session (injected via dependency).
#     :raises HTTPException: If the comment does not exist.
#     """
#     comment_repo = CommentsRepository(db)
#     comment = await comment_repo.get_comment_by_id(comment_id)
#     if not comment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
#         )
#     await comment_repo.delete_comment(comment_id)
