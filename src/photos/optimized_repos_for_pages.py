from sqlalchemy import insert, func, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy.orm import selectinload, joinedload, aliased

from src.models.models import Photo, photo_tags, User, PhotoRating, Comment, Tag, Reaction
from src.tags.repos import TagRepository

MAX_TAGS_COUNT = 5


class PhotoRepositoryOptimized:
    def __init__(self, session: AsyncSession):
        """
        Initialize the PhotoRepository.

        Args:
            session (AsyncSession): The database session.
        """
        self.session = session

    async def data_for_photo_page(self, photo_id: int, current_user_id: int = None):
        PhotoOwner = aliased(User)
        CommentUser = aliased(User)

        result = await self.session.execute(
            select(
                Photo,
                PhotoOwner.username.label("photo_owner"),
                PhotoOwner.avatar_url.label("photo_owner_avatar"),
                PhotoOwner.id.label("owner_id"),
                Tag.name,
                Comment.id.label("comment_id"),
                Comment.content.label("comment_content"),
                Comment.created_at.label("comment_created_at"),
                Comment.user_id.label("comment_user_id"),
                CommentUser.username.label("comment_username"),
                CommentUser.avatar_url.label("comment_avatar")
            )
            .join(PhotoOwner, Photo.owner_id == PhotoOwner.id)
            .outerjoin(Comment, Photo.id == Comment.photo_id)
            .outerjoin(CommentUser, Comment.user_id == CommentUser.id)
            .outerjoin(photo_tags, Photo.id == photo_tags.c.photo_id)
            .outerjoin(Tag, Tag.id == photo_tags.c.tag_id)
            .where(Photo.id == photo_id)
            .distinct()
        )

        rows = result.mappings().all()

        if not rows:
            return None

        photo_info = {
            "id": photo_id,
            "url_link": rows[0]["Photo"].url_link,
            "description": rows[0]["Photo"].description,
            "created_at": rows[0]["Photo"].created_at.isoformat() if rows[0]["Photo"].created_at else None,
            "username": rows[0]["photo_owner"],
            "avatar_url": rows[0]["photo_owner_avatar"],
            "owner_id": rows[0]["owner_id"],
            "tags": list({row["name"] for row in rows if row["name"] is not None}),
            "comments": []
        }

        for row in rows:
            if row["comment_id"] is not None:
                comment_exists = any(c["id"] == row["comment_id"] for c in photo_info["comments"])
                if not comment_exists:
                    can_edit = current_user_id and current_user_id == row["comment_user_id"]
                    can_delete = (current_user_id and
                                  (current_user_id == row["comment_user_id"] or
                                   current_user_id == photo_info["owner_id"] or
                                   current_user_id == 3))

                    photo_info["comments"].append({
                        "id": row["comment_id"],
                        "content": row["comment_content"],
                        "created_at": row["comment_created_at"].isoformat() if row["comment_created_at"] else None,
                        "username": row["comment_username"],
                        "avatar_url": row["comment_avatar"],
                        "user": {
                            "username": row["comment_username"],
                            "avatar_url": row["comment_avatar"]
                        },
                        "permissions": {
                            "can_edit": can_edit,
                            "can_delete": can_delete
                        }
                    })

        return photo_info