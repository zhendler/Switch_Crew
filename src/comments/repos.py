from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.comments.schemas import CommentResponse
from src.models.models import Comment


class CommentsRepository:
    """
    Repository for managing operations related to comments in the database.

    This repository provides methods to create, retrieve, update, and delete comments.
    It interacts with the database using an asynchronous SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the CommentsRepository with a database session.

        :param session: An asynchronous SQLAlchemy session used for database operations.
        """
        self.session = session

    async def create_comment(
        self, user_id: int, photo_id: int, content: str
    ) -> Comment:
        """
        Creates a new comment in the database.

        :param user_id: The ID of the user creating the comment.
        :param photo_id: The ID of the photo the comment is associated with.
        :param content: The text content of the comment.
        :return: The created Comment object.
        """
        new_comment = Comment(user_id=user_id, photo_id=photo_id, content=content)
        self.session.add(new_comment)
        await self.session.commit()
        await self.session.refresh(new_comment)
        return new_comment

    async def get_comments_by_user(self, user_id: int):
        """
        Retrieves all comments made by a specific user.

        :param user_id: The ID of the user whose comments are to be retrieved.
        :return: A list of Comment objects.
        """
        query = select(Comment).where(Comment.user_id == user_id)
        comments = await self.session.execute(query)
        return comments.scalars().all()

    async def get_comments_by_photo(
        self, photo_id: int
    ) -> list[Comment:CommentResponse]:
        """
        Retrieves all comments associated with a specific photo.

        :param photo_id: The ID of the photo whose comments are to be retrieved.
        :return: A list of Comment objects.
        """
        result = await self.session.execute(
            select(Comment).where(Comment.photo_id == photo_id)
        )
        return result.scalars().all()

    async def update_comment(
        self, comment_id: int, user_id: int, content: str
    ) -> Comment:
        """
        Updates the content of an existing comment.

        :param comment_id: The ID of the comment to be updated.
        :param user_id: The ID of the user attempting to update the comment.
        :param content: The new content for the comment.
        :return: The updated Comment object.
        :raises HTTPException: If the comment is not found or the user lacks permission to update it.
        """
        comment = await self.session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this comment",
            )

        comment.content = content
        import datetime

        comment.updated_at = datetime.datetime.now(datetime.timezone.utc)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int) -> None:
        """
        Deletes a comment by its ID.

        :param comment_id: The ID of the comment to be deleted.
        :raises HTTPException: If the comment is not found.
        """
        comment = await self.session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        await self.session.delete(comment)
        await self.session.commit()

    async def get_comment_by_id(self, comment_id: int) -> Comment | None:
        """
        Retrieves a comment by its ID.

        :param comment_id: The ID of the comment to be retrieved.
        :return: The Comment object if found, otherwise None.
        """
        return await self.session.get(Comment, comment_id)

    async def reply_to_comment_with_comment(self, comment_id: int, user_id: int, content: str) -> Comment:
        new_comment = Comment(user_id=user_id, parent_id=comment_id, content=content)
        self.session.add(new_comment)
        await self.session.commit()
        await self.session.refresh(new_comment)
        return new_comment