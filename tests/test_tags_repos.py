import unittest
from unittest.mock import AsyncMock, MagicMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from src.tags.repos import TagRepository
from src.models.models import Tag, Photo
from fastapi import HTTPException, status


class TestTagRepository(unittest.IsolatedAsyncioTestCase):

    async def test_create_tag_when_tag_does_not_exist(self):
        mock_db = AsyncMock(AsyncSession)

        mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=None)

        tag_repo = TagRepository(mock_db)

        tag_name = "new_tag"

        new_tag = await tag_repo.create_tag(tag_name)

        self.assertEqual(new_tag.name, tag_name)
        self.assertEqual(new_tag.id, None)

        mock_db.add(new_tag)
        mock_db.commit.assert_called_once_with()
        mock_db.refresh.assert_called_once_with(new_tag)

    async def test_create_tag_when_tag_exists(self):
        mock_db = AsyncMock(AsyncSession)

        mock_existing_tag = Tag(id=1, name="existing_tag")

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing_tag
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        tag_name = "existing_tag"

        existing_tag = await tag_repo.create_tag(tag_name)

        self.assertEqual(existing_tag.name, "existing_tag")
        self.assertEqual(existing_tag.id, 1)

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    async def test_get_tag_by_name_when_tag_exists(self):
        mock_existing_tag = Tag(id=1, name="existing_tag")

        mock_db = AsyncMock(AsyncSession)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing_tag
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        tag_name = "existing_tag"

        existing_tag = await tag_repo.get_tag_by_name(tag_name)

        self.assertEqual(existing_tag.name, "existing_tag")
        self.assertEqual(existing_tag.id, 1)

    async def test_get_tag_by_name_when_tag_does_not_exist(self):
        mock_db = AsyncMock(AsyncSession)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        tag_name = "non-existent_tag"

        with self.assertRaises(HTTPException) as context:
            await tag_repo.get_tag_by_name(tag_name)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Tag not found!")

    async def test_get_all_tags(self):
        mock_existing_tag = Tag(id=1, name="existing_tag")
        mock_existing_tag2 = Tag(id=2, name="existing_tag2")

        mock_db = AsyncMock(AsyncSession)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            mock_existing_tag,
            mock_existing_tag2,
        ]
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        existing_tags = await tag_repo.get_all_tags()

        self.assertEqual(existing_tags, [mock_existing_tag, mock_existing_tag2])

    async def test_delete_tag_by_name_when_tag_exist(self):
        mock_db = AsyncMock(AsyncSession)

        mock_existing_tag = Tag(id=1, name="existing_tag")

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing_tag
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        await tag_repo.delete_tag_by_name(mock_existing_tag.name)

        mock_db.delete.assert_called_once_with(mock_existing_tag)
        mock_db.commit.assert_called_once()

    async def test_delete_tag_by_name_when_tag_does_not_exist(self):
        mock_db = AsyncMock(AsyncSession)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        tag_name = "non-existent_tag"

        with self.assertRaises(HTTPException) as context:
            await tag_repo.delete_tag_by_name(tag_name)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Tag not found!")

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_update_tag_name_when_tag_exist(self):
        mock_db = AsyncMock(AsyncSession)

        mock_existing_tag = Tag(id=1, name="existing_tag")

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_existing_tag
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        updated_tag = await tag_repo.update_tag_name(
            mock_existing_tag.name, "existing_tag2"
        )

        self.assertEqual(updated_tag.name, "existing_tag2")
        self.assertEqual(updated_tag.id, 1)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_existing_tag)

    async def test_update_tag_name_when_tag_does_not_exist(self):
        mock_db = AsyncMock(AsyncSession)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)

        tag_name = "non-existent_tag"

        with self.assertRaises(HTTPException) as context:
            await tag_repo.update_tag_name(tag_name, "non-existent_tag2")

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Tag not found!")

        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    async def test_get_photos_by_tag_when_tag_exist(self):
        mock_db = AsyncMock(AsyncSession)
        existent_tag1 = Tag(name="existent_tag")
        existent_tag2 = Tag(name="existent_tag2")

        mock_existing_photo1 = Photo(
            id=1, url_link="existing_photo1", owner_id=1, tags=[existent_tag1]
        )
        mock_existing_photo2 = Photo(
            id=2,
            url_link="existing_photo2",
            owner_id=2,
            tags=[existent_tag1, existent_tag2],
        )

        mock_result = Mock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            mock_existing_photo1,
            mock_existing_photo2,
        ]
        mock_db.execute.return_value = mock_result

        tag_repo = TagRepository(mock_db)
        tag_repo.get_tag_by_name = AsyncMock(return_value=existent_tag1)

        tag_name = "existent_tag"

        photos = await tag_repo.get_photos_by_tag(tag_name)

        self.assertEqual(photos, [mock_existing_photo1, mock_existing_photo2])


if __name__ == "__main__":
    unittest.main()
