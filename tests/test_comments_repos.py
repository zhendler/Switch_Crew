import unittest
from unittest.mock import AsyncMock, MagicMock, Mock

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Comment
from src.comments.repos import CommentsRepository


class TestCommentsRepository(unittest.IsolatedAsyncioTestCase):
    async def test_create_comment_success(self):
        # Arrange
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        repo = CommentsRepository(mock_session)
        user_id = 1
        photo_id = 2
        content = "Test comment"

        # Очікуваний об'єкт коментаря
        expected_comment = Comment(user_id=user_id, photo_id=photo_id, content=content)

        # Mock повернення ID для коментаря
        mock_session.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        # Act
        result = await repo.create_comment(user_id, photo_id, content)

        # Assert
        # Перевіряємо, чи викликали add з будь-яким об'єктом Comment
        mock_session.add.assert_called_once()
        self.assertIsInstance(mock_session.add.call_args[0][0], Comment)  # Перевіряємо тип об'єкта

        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

        # Перевіряємо атрибути поверненого об'єкта
        self.assertEqual(result.user_id, user_id)
        self.assertEqual(result.photo_id, photo_id)
        self.assertEqual(result.content, content)
        self.assertEqual(result.id, 1)

    async def test_create_comment_sqlalchemy_error(self):
        # Arrange
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))  # Симуляція помилки

        repo = CommentsRepository(mock_session)
        user_id = 1
        photo_id = 2
        content = "Test comment"

        # Act & Assert
        with self.assertRaises(SQLAlchemyError):
            await repo.create_comment(user_id, photo_id, content)

        mock_session.add.assert_called_once()  # Перевірка, що add викликався
        mock_session.commit.assert_awaited_once()  # commit теж викликано
        mock_session.refresh.assert_not_called()  # refresh не викликано через помилку

    async def test_get_comments_by_user_success(self):
        # Arrange
        mock_session = AsyncMock(AsyncSession)

        # Створюємо моки для execute, які повертають потрібний результат
        mock_execute = Mock()
        mock_execute.scalars.return_value.all.return_value = [
            Comment(user_id=1, photo_id=2, content="Test comment 1"),
            Comment(user_id=1, photo_id=3, content="Test comment 2")
        ]

        mock_session.execute.return_value = mock_execute

        repo = CommentsRepository(mock_session)
        user_id = 1

        # Act
        result = await repo.get_comments_by_user(user_id)

        # Assert
        mock_session.execute.assert_awaited_once()  # Перевіряємо, що execute було викликано
        mock_execute.scalars.return_value.all.assert_called_once()  # Перевіряємо виклик all()

        # Перевіряємо, чи результат містить два коментарі
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, "Test comment 1")
        self.assertEqual(result[1].content, "Test comment 2")

    async def test_get_comments_by_photo_success(self):
        # Arrange
        mock_session = AsyncMock()  # Створюємо мок сесії
        mock_execute = Mock()

        # Створюємо моки для результату виконання запиту
        mock_execute.scalars.return_value.all.return_value = [
            Comment(user_id=1, photo_id=2, content="Test comment 1"),
            Comment(user_id=2, photo_id=2, content="Test comment 2")
        ]

        # Мокаємо метод execute
        mock_session.execute.return_value = mock_execute

        # Створюємо об'єкт репозиторію
        repo = CommentsRepository(mock_session)
        photo_id = 2  # Приклад photo_id для тесту

        # Act
        result = await repo.get_comments_by_photo(photo_id)

        # Assert
        mock_session.execute.assert_awaited_once()  # Перевіряємо виклик execute
        mock_execute.scalars.return_value.all.assert_called_once()  # Перевіряємо виклик all()

        # Перевіряємо, чи результат містить два коментарі
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, "Test comment 1")
        self.assertEqual(result[1].content, "Test comment 2")

    async def test_update_comment_success(self):
        # Arrange
        mock_session = AsyncMock()
        comment = Comment(id=1, user_id=1, photo_id=2, content="Old content", updated_at=None)
        mock_session.get.return_value = comment

        repo = CommentsRepository(mock_session)
        comment_id = 1
        user_id = 1
        new_content = "Updated content"

        # Act
        result = await repo.update_comment(comment_id, user_id, new_content)

        # Assert
        mock_session.get.assert_awaited_once_with(Comment, comment_id)
        mock_session.commit.assert_awaited_once()
        self.assertEqual(result.content, new_content)
        self.assertIsNotNone(result.updated_at)

    async def test_update_comment_not_found(self):
        # Arrange
        mock_session = AsyncMock()
        mock_session.get.return_value = None  # Мокаємо відсутній коментар

        repo = CommentsRepository(mock_session)
        comment_id = 999  # Невідомий comment_id
        user_id = 1
        new_content = "Updated content"

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await repo.update_comment(comment_id, user_id, new_content)
        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)

    async def test_delete_comment_success(self):
        # Arrange
        mock_session = AsyncMock()
        comment = Comment(id=1, user_id=1, photo_id=2, content="Content to delete")
        mock_session.get.return_value = comment

        repo = CommentsRepository(mock_session)
        comment_id = 1

        # Act
        await repo.delete_comment(comment_id)

        # Assert
        mock_session.get.assert_awaited_once_with(Comment, comment_id)
        mock_session.delete.assert_awaited_once_with(comment)
        mock_session.commit.assert_awaited_once()

    async def test_delete_comment_not_found(self):
        # Arrange
        mock_session = AsyncMock()
        mock_session.get.return_value = None  # Мокаємо відсутній коментар

        repo = CommentsRepository(mock_session)
        comment_id = 999  # Невідомий comment_id

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await repo.delete_comment(comment_id)
        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)

    async def test_get_comment_by_photo_id_success(self):
        # Arrange
        mock_session = AsyncMock()
        mock_execute = Mock()
        mock_execute.scalars.return_value.all.return_value = [
            Comment(user_id=1, photo_id=2, content="Test comment 1"),
            Comment(user_id=2, photo_id=2, content="Test comment 2")
        ]
        mock_session.execute.return_value = mock_execute

        repo = CommentsRepository(mock_session)
        photo_id = 2

        # Act
        result = await repo.get_comment_by_photo_id(photo_id)

        # Assert
        mock_session.execute.assert_awaited_once()
        mock_execute.scalars.return_value.all.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, "Test comment 1")
        self.assertEqual(result[1].content, "Test comment 2")


if __name__ == "__main__":
    unittest.main()
