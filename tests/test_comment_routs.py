# import unittest
# from unittest.mock import AsyncMock, patch, MagicMock
# from fastapi.testclient import TestClient
# from fastapi import status, HTTPException
#
# from main import app  # Заміни на твій основний файл, де підключено роутер
# from src.comments.schemas import CommentCreate, CommentResponse
#
# class TestCreateCommentRoute(unittest.TestCase):
#     def setUp(self):
#         self.client = TestClient(app)
#         self.comment_repo_mock = AsyncMock()
#         self.user_mock = MagicMock(id=1)  # Мок об'єкта User
#         self.db_mock = AsyncMock()
#
#         # Патчимо залежності
#         self.get_current_user_patcher = patch("src.api.dependencies.get_current_user", return_value=self.user_mock)
#         self.get_db_patcher = patch("src.api.dependencies.get_db", return_value=self.db_mock)
#         self.comments_repo_patcher = patch("src.repositories.comments.CommentsRepository", return_value=self.comment_repo_mock)
#
#         self.mock_get_current_user = self.get_current_user_patcher.start()
#         self.mock_get_db = self.get_db_patcher.start()
#         self.mock_comments_repo = self.comments_repo_patcher.start()
#
#     def tearDown(self):
#         patch.stopall()
#
#     def test_create_comment_success(self):
#         # Arrange
#         comment_data = {"photo_id": 2, "content": "Test comment"}
#         expected_response = {"id": 1, "user_id": self.user_mock.id, "photo_id": 2, "content": "Test comment"}
#         self.comment_repo_mock.create_comment.return_value = expected_response
#
#         # Act
#         response = self.client.post("/comments/", json=comment_data)
#
#         # Assert
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.json(), expected_response)
#         self.comment_repo_mock.create_comment.assert_awaited_once_with(self.user_mock.id, 2, "Test comment")
#
#     def test_create_comment_invalid_data(self):
#         # Arrange
#         invalid_data = {"photo_id": 2}  # Відсутній контент
#
#         # Act
#         response = self.client.post("/comments/", json=invalid_data)
#
#         # Assert
#         self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
#
#     def test_create_comment_repository_error(self):
#         # Arrange
#         comment_data = {"photo_id": 2, "content": "Test comment"}
#         self.comment_repo_mock.create_comment.side_effect = HTTPException(status_code=500, detail="Internal Server Error")
#
#         # Act
#         response = self.client.post("/comments/", json=comment_data)
#
#         # Assert
#         self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
#         self.assertEqual(response.json()["detail"], "Internal Server Error")
#         self.comment_repo_mock.create_comment.assert_awaited_once_with(self.user_mock.id, 2, "Test comment")
