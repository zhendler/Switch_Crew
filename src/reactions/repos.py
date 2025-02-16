from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, insert, func

from .schemas import ReactionResponse
from ..models.models import Tag, Photo, Reaction, User, photo_reactions
from ..photos.repos import PhotoRepository


class ReactionRepository:
    """
    Repository for managing tags in the database.
    Provides methods to retrieve, create, update, and delete tags, as well as retrieve photos associated with a specific tag.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the TagRepository with an asynchronous database session.

        :param db: An instance of AsyncSession for interacting with the database.
        """
        self.db = db

    async def create_reaction(self, reaction_name):
        new_reaction = Reaction(name=reaction_name)
        self.db.add(new_reaction)
        await self.db.commit()
        await self.db.refresh(new_reaction)
        return new_reaction


    async def add_reaction(
        self, photo_id: int, user_id: int, reaction_id: int
    ) -> ReactionResponse or None:
        photo_repo = PhotoRepository(self.db)
        photo = await photo_repo.get_photo_by_id(photo_id)
        if not photo:
            raise ValueError(f"Photo not found")

        existing_reaction = await self.get_reaction_by_user_and_photo(photo_id, user_id)

        if existing_reaction:
            if existing_reaction.reaction_id == reaction_id:
                await self.delete_reaction(photo_id, user_id)
                return None
            else:
                await self.delete_reaction(photo_id, user_id)

        reaction = await self.db.execute(select(Reaction).filter_by(id=reaction_id))
        reaction = reaction.scalar_one_or_none()

        reaction_photo = insert(photo_reactions).values(photo_id=photo_id, user_id=user_id, reaction_id=reaction.id)
        await self.db.execute(reaction_photo)
        await self.db.commit()

        return await self.get_reaction_by_user_and_photo(photo_id, user_id)

    async def get_reaction_by_user_and_photo(self, photo_id: int, user_id: int):
        query = select(
            photo_reactions.c.reaction_id,
            photo_reactions.c.user_id,
            photo_reactions.c.photo_id,
            photo_reactions.c.created_at,
            Reaction.name
        ).join(
            Reaction, Reaction.id == photo_reactions.c.reaction_id
        ).where(
            (photo_reactions.c.photo_id == photo_id) &
            (photo_reactions.c.user_id == user_id)
        )

        result = await self.db.execute(query)
        reaction_data = result.fetchone()

        if reaction_data:
            return ReactionResponse(
                reaction_id=reaction_data.reaction_id,
                name=reaction_data.name,
                user_id=reaction_data.user_id,
                photo_id=reaction_data.photo_id,
                created_at=reaction_data.created_at
            )
        return None

    async def get_all_reactions_by_photo(self, photo_id):
        query = select(
            photo_reactions.c.reaction_id,
            photo_reactions.c.user_id,
            photo_reactions.c.photo_id,
            photo_reactions.c.created_at,
            Reaction.name
        ).join(
            Reaction, Reaction.id == photo_reactions.c.reaction_id
        ).where(
            (photo_reactions.c.photo_id == photo_id)
        )

        result = await self.db.execute(query)
        reaction_data_list = result.fetchall()
        if reaction_data_list:
            reactions = [
                ReactionResponse(
                    reaction_id=reaction_data.reaction_id,
                    name=reaction_data.name,
                    user_id=reaction_data.user_id,
                    photo_id=reaction_data.photo_id,
                    created_at=reaction_data.created_at
                )
                for reaction_data in reaction_data_list
            ]

            return reactions
        else:
            return "Reactions not found"

    async def change_reaction(self, photo_id, user_id, new_reaction_id):
        await self.db.execute(
            photo_reactions.update()
            .where(
                (photo_reactions.c.photo_id == photo_id) &
                (photo_reactions.c.user_id == user_id)
            )
            .values(reaction_id=new_reaction_id)
        )
        await self.db.commit()
        reaction = await self.get_reaction_by_user_and_photo(photo_id, user_id)

        return reaction

    async def delete_reaction(self, photo_id, user_id):
        query = photo_reactions.delete().where(
            (photo_reactions.c.photo_id == photo_id) &
            (photo_reactions.c.user_id == user_id)
        )
        await self.db.execute(query)
        await self.db.commit()
        return "Reaction was deleted"

    async def get_reaction_counts(self, photo_id: int) -> list[int]:
        reaction_counts = [0] * 9

        query = (
            select(photo_reactions.c.reaction_id, func.count().label("count"))
            .where(photo_reactions.c.photo_id == photo_id)
            .group_by(photo_reactions.c.reaction_id)
        )

        result = await self.db.execute(query)
        rows = result.all()

        for row in rows:
            reaction_id = row.reaction_id
            count = row.count
            if 1 <= reaction_id <= 8:
                reaction_counts[reaction_id] = count

        return reaction_counts

    async def get_all_reactions_in_feed(self, photos, user):
        reaction_data = {}
        for photo in photos:
            reaction_counts = await self.get_reaction_counts(photo.id)
            reaction_active = await self.get_reaction_by_user_and_photo(photo.id, user.id) if user else None
            reaction_data[photo.id] = {
                "reaction_counts": reaction_counts,
                "reaction_active": reaction_active.reaction_id if reaction_active else None
            }
        return reaction_data