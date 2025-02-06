import unittest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from src.reactions.repos import ReactionRepository, Reaction, photo_reactions, Photo, User

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

class TestReactionRepository(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(
            DATABASE_URL,
            poolclass=StaticPool,
        )
        async with self.engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.run_sync(Reaction.metadata.create_all, checkfirst=True)
            await conn.run_sync(Photo.metadata.create_all, checkfirst=True)
            await conn.run_sync(User.metadata.create_all, checkfirst=True)
            await conn.run_sync(photo_reactions.metadata.create_all, checkfirst=True)

        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.db_session = self.async_session()
        self.reaction_repo = ReactionRepository(self.db_session)

    async def asyncTearDown(self):
        await self.db_session.close()
        await self.engine.dispose()

    async def test_create_reaction(self):
        reaction_name = "like"
        reaction = await self.reaction_repo.create_reaction(reaction_name)
        self.assertEqual(reaction.name, reaction_name)
        self.assertIsNotNone(reaction.id)

    async def test_add_reaction(self):
        user = User(id=1, username="test_user", email="test@example.com", hashed_password="test_hash")
        photo = Photo(id=1, owner_id=1, url_link="https://example.com/photo.jpg")
        reaction = Reaction(id=1, name="like")
        self.db_session.add(user)
        self.db_session.add(photo)
        self.db_session.add(reaction)
        await self.db_session.commit()

        reaction_response = await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)
        self.assertIsNotNone(reaction_response)
        self.assertEqual(reaction_response.reaction_id, 1)
        self.assertEqual(reaction_response.user_id, 1)
        self.assertEqual(reaction_response.photo_id, 1)

        reaction_response = await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)
        self.assertIsNone(reaction_response)

    async def test_get_reaction_by_user_and_photo(self):
        user = User(id=1, username="test_user", email="test@example.com", hashed_password="test_hash")
        photo = Photo(id=1, owner_id=1, url_link="https://example.com/photo.jpg")
        reaction = Reaction(id=1, name="like")
        self.db_session.add(user)
        self.db_session.add(photo)
        self.db_session.add(reaction)
        await self.db_session.commit()

        await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)

        reaction_response = await self.reaction_repo.get_reaction_by_user_and_photo(photo_id=1, user_id=1)
        self.assertIsNotNone(reaction_response)
        self.assertEqual(reaction_response.reaction_id, 1)
        self.assertEqual(reaction_response.user_id, 1)
        self.assertEqual(reaction_response.photo_id, 1)

    async def test_get_all_reactions_by_photo(self):

        user1 = User(id=1, username="test_user", email="test@example.com", hashed_password="test_hash")
        user2 = User(id=2, username="test_user2", email="test2@example.com", hashed_password="test_hash2")
        photo = Photo(id=1, owner_id=1, url_link="https://example.com/photo.jpg")
        reaction1 = Reaction(id=1, name="like")
        reaction2 = Reaction(id=2, name="dislike")
        self.db_session.add(user1)
        self.db_session.add(user2)
        self.db_session.add(photo)
        self.db_session.add(reaction1)
        self.db_session.add(reaction2)
        await self.db_session.commit()

        await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)
        await self.reaction_repo.add_reaction(photo_id=1, user_id=2, reaction_id=2)

        reactions = await self.reaction_repo.get_all_reactions_by_photo(photo_id=1)
        self.assertEqual(len(reactions), 2)
        self.assertEqual(reactions[0].reaction_id, 1)
        self.assertEqual(reactions[1].reaction_id, 2)

    async def test_change_reaction(self):
        user = User(id=1, username="test_user", email="test@example.com", hashed_password="test_hash")
        photo = Photo(id=1, owner_id=1, url_link="https://example.com/photo.jpg")
        reaction1 = Reaction(id=1, name="like")
        reaction2 = Reaction(id=2, name="dislike")
        self.db_session.add(user)
        self.db_session.add(photo)
        self.db_session.add(reaction1)
        self.db_session.add(reaction2)
        await self.db_session.commit()

        await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)

        updated_reaction = await self.reaction_repo.change_reaction(photo_id=1, user_id=1, new_reaction_id=2)
        self.assertEqual(updated_reaction.reaction_id, 2)

    async def test_delete_reaction(self):
        user = User(id=1, username="test_user", email="test@example.com", hashed_password="test_hash")
        photo = Photo(id=1, owner_id=1, url_link="https://example.com/photo.jpg")
        reaction = Reaction(id=1, name="like")
        self.db_session.add(user)
        self.db_session.add(photo)
        self.db_session.add(reaction)
        await self.db_session.commit()

        await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)

        result = await self.reaction_repo.delete_reaction(photo_id=1, user_id=1)
        self.assertEqual(result, "Reaction was deleted")

        reaction_response = await self.reaction_repo.get_reaction_by_user_and_photo(photo_id=1, user_id=1)
        self.assertIsNone(reaction_response)

    async def test_get_reaction_counts(self):
        user1 = User(id=1, username="test_user1", email="test1@example.com", hashed_password="test_hash1")
        user2 = User(id=2, username="test_user2", email="test2@example.com", hashed_password="test_hash2")
        photo = Photo(id=1, owner_id=1, url_link="https://example.com/photo.jpg")
        reaction1 = Reaction(id=1, name="like")
        reaction2 = Reaction(id=2, name="dislike")
        self.db_session.add(user1)
        self.db_session.add(user2)
        self.db_session.add(photo)
        self.db_session.add(reaction1)
        self.db_session.add(reaction2)
        await self.db_session.commit()

        await self.reaction_repo.add_reaction(photo_id=1, user_id=1, reaction_id=1)
        await self.reaction_repo.add_reaction(photo_id=1, user_id=2, reaction_id=2)

        reaction_counts = await self.reaction_repo.get_reaction_counts(photo_id=1)
        self.assertEqual(reaction_counts[1], 1)
        self.assertEqual(reaction_counts[2], 1)

if __name__ == "__main__":
    unittest.main()