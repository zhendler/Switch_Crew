from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.schemas import RoleEnum
from src.auth.utils import get_current_user, RoleChecker
from src.comments.repos import CommentsRepository
from src.comments.schemas import CommentResponse, CommentCreate
from src.models.models import User

router =APIRouter()

FORALL = [Depends(RoleChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR, RoleEnum.USER]))]
FORMODER = [Depends(RoleChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR]))]


@router.post("/", response_model=CommentResponse,
             dependencies= FORALL,
             status_code=status.HTTP_201_CREATED)
async def create_comment(comment: CommentCreate,
                        user: User = Depends (get_current_user),
                        db:AsyncSession = Depends(get_db)):
    comment_repo = CommentsRepository(db)
    return await comment_repo.create_comment(user.id, comment.photo_id, comment.content)


@router.get("/user/",
            response_model=list[CommentResponse],
            dependencies= FORALL)
async def get_user_comments(user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    comment_repo = CommentsRepository(db)
    return await comment_repo.get_comments_by_user(user.id)

@router.get("/photo/{photo_id}/",
            response_model=list[CommentResponse],
            dependencies= FORALL)
async def get_photo_comments( photo_id: int, user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    comment_repo = CommentsRepository(db)
    return await comment_repo.get_comments_by_photo(photo_id)


@router.get("/user/{user_id}/comments",
            response_model=list[CommentResponse],
            dependencies= FORMODER)
async def get_comments_by_user(user_id: int,
                        db: AsyncSession = Depends(get_db)):
    comment_repo = CommentsRepository(db)
    return await comment_repo.get_comments_by_user(user_id)


@router.put("/{comment_id}/",
            response_model=CommentResponse,
            dependencies= FORALL)
async def update_comment(
    comment_id: int,
    content: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    comment_repo = CommentsRepository(db)
    return await comment_repo.update_comment(comment_id=comment_id,
                                             user_id=user.id,
                                             content=content)


@router.delete("/{comment_id}/",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies= FORALL)
async def delete_own_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    comment_repo = CommentsRepository(db)
    comment = await comment_repo.get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot delete this comment")
    await comment_repo.delete_comment(comment_id)


@router.delete("/admin/{comment_id}/",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=FORMODER)
async def delete_any_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db)
):
    comment_repo = CommentsRepository(db)
    comment = await comment_repo.get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    await comment_repo.delete_comment(comment_id)








