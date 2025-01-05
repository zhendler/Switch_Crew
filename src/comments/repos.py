from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.comments.schemas import CommentResponse
from src.models.models import Comment


class CommentsRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_comment(self,user_id: int, photo_id: int, content: str) ->Comment:
        new_comment = Comment(user_id=user_id, photo_id=photo_id, content=content)
        self.session.add(new_comment)
        await self.session.commit()
        await self.session.refresh(new_comment)
        return new_comment


    async def get_comments_by_user(self, user_id: int) -> list[Comment:CommentResponse]:
        result = await self.session.execute(
            select(Comment).where(Comment.user_id == user_id)
        )
        return result.scalars().all()

    async def get_comments_by_photo(self, photo_id: int) -> list[Comment:CommentResponse]:
        result = await self.session.execute(
            select(Comment).where(Comment.photo_id == photo_id)
        )
        return result.scalars().all()

    async def update_comment(self, comment_id: int, user_id: int, content: str) -> Comment:
        comment = await self.session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You do not have permission to update this comment")

        comment.content = content
        import datetime
        comment.updated_at = datetime.datetime.now(datetime.timezone.utc)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int) -> None:
        comment = await self.session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        await self.session.delete(comment)
        await self.session.commit()

    async def get_comment_by_id(self, comment_id: int) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def get_comment_by_photo_id(self, photo_id: int) -> list[Comment:CommentResponse] | None:
        query = select(Comment).where(Comment.photo_id == photo_id)
        result = await self.session.execute(query)
        return result.scalars().all()



