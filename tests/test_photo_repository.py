import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.photos.repos import PhotoRepository, Photo, User
from sqlalchemy.exc import SQLAlchemyError


class TestPhotoRepository(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_session = AsyncMock(spec=AsyncSession)
        self.photo_repo = PhotoRepository(session=self.mock_session)

    async def test_update_photo_description(self):
        test_photo = MagicMock()
        test_photo.description = "Old description"
        test_photo.owner_id = 1
        self.mock_session.get.return_value = test_photo
        updated_photo = await self.photo_repo.update_photo_description(
            photo_id=1,
            description="New description",
            user_id=1,
        )
        self.assertEqual(updated_photo.description, "New description")
        self.mock_session.commit.assert_called_once()

    async def test_get_photo_by_id(self):
        mock_photo = MagicMock(spec=Photo)
        mock_photo.id = 1
        mock_photo.description = "Test description"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_photo
        self.mock_session.execute.return_value = mock_result

        photo_id = 1
        photo = await self.photo_repo.get_photo_by_id(photo_id)

        self.mock_session.execute.assert_awaited_once()
        args, _ = self.mock_session.execute.await_args
        executed_query = args[0]

        expected_query = select(Photo).filter(Photo.id == photo_id)
        self.assertEqual(str(executed_query), str(expected_query))

        self.assertEqual(photo, mock_photo)
        self.assertEqual(photo.id, 1)
        self.assertEqual(photo.description, "Test description")

    async def test_create_photo(self):
        user = User(id=1)
        tags = ["tag1", "tag2", "tag3"]

        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.refresh.return_value = None

        with patch.object(self.photo_repo, "create_photo") as mock_create_photo:
            mock_create_photo.return_value = Photo(
                url_link="http://example.com", description="test", owner_id=1
            )
            result = await self.photo_repo.create_photo(
                "http://example.com", "test", user, tags
            )
            self.assertEqual(result, mock_create_photo.return_value)

    async def test_create_photo_error(self):
        self.mock_session.add.side_effect = SQLAlchemyError("Database error")
        with self.assertRaises(SQLAlchemyError):
            await self.photo_repo.create_photo(
                "http://example.com", "test", User(id=1), []
            )