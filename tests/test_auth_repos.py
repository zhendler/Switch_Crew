from fastapi import HTTPException, status
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from starlette.datastructures import UploadFile
from src.models.models import User, Role
from src.auth.repos import UserRepository, RoleRepository
from src.auth.schemas import UserCreate, RoleEnum


class TestUserRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_session = AsyncMock(spec=AsyncSession)
        self.mock_session.add = MagicMock()
        self.user_repo = UserRepository(self.mock_session)
        self.role_repo = RoleRepository(self.mock_session)

    @patch("src.auth.repos.RoleRepository.get_role_by_name")
    @patch("src.auth.repos.get_password_hash")
    async def test_create_user(self, mock_get_password_hash, mock_get_role_by_name):
        user_create = UserCreate(
            username="newuser", 
            email="newuser@example.com", 
            password="password123"
        )
        mock_get_password_hash.return_value = "hashed_password"
        mock_user_role = MagicMock()
        mock_user_role.id = 1
        mock_get_role_by_name.return_value = mock_user_role
        mock_execute_result = MagicMock()
        mock_execute_result.scalars().first.return_value = None
        self.mock_session.execute.return_value = mock_execute_result
        created_user = await self.user_repo.create_user(user_create)
        self.assertEqual(created_user.username, "newuser")
        self.assertEqual(created_user.email, "newuser@example.com")
        self.assertEqual(created_user.hashed_password, "hashed_password")
        self.assertEqual(created_user.role_id, mock_user_role.id)
        self.assertFalse(created_user.is_active)
        self.mock_session.add.assert_called_once_with(created_user)
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once_with(created_user)
        mock_get_role_by_name.assert_called_once_with(RoleEnum.ADMIN)

    
    @patch("src.auth.repos.AsyncSession")
    async def test_get_user_by_email(self, MockSession):
        mock_user = User(
            username="testuser", 
            email="test@example.com", 
            hashed_password="hashed_password", 
            role_id=1, 
        )
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = mock_user
        mock_session_instance = MockSession.return_value
        mock_session_instance.execute = AsyncMock(return_value=mock_execute_result)
        self.user_repo = UserRepository(mock_session_instance)
        user = await self.user_repo.get_user_by_email("test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        expected_query = select(User).where(User.email == "test@example.com")
        actual_query_str = str(mock_session_instance.execute.call_args[0][0])
        expected_query_str = str(expected_query)
        self.assertEqual(actual_query_str, expected_query_str)

    @patch("src.auth.repos.AsyncSession")
    async def test_get_user_by_username(self, MockSession):
        mock_user = User(username="testuser", email="test@example.com")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        self.mock_session.execute.return_value = mock_result
        user = await self.user_repo.get_user_by_username("testuser")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        expected_query = select(User).where(User.username == "testuser")
        actual_query_str = str(self.mock_session.execute.call_args[0][0])
        expected_query_str = str(expected_query)
        self.assertEqual(actual_query_str, expected_query_str)

    @patch("src.auth.repos.AsyncSession")
    async def test_get_user_by_id(self, MockSession):
        mock_user = User(id=1, username="testuser", email="test@example.com")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        self.mock_session.execute.return_value = mock_result
        user = await self.user_repo.get_user_by_id(1)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.username, "testuser")
        expected_query = select(User).where(User.id == 1)
        actual_query_str = str(self.mock_session.execute.call_args[0][0])
        expected_query_str = str(expected_query)
        self.assertEqual(actual_query_str, expected_query_str)
        
    @patch("cloudinary.uploader.upload")
    async def test_upload_to_cloudinary_success(self, mock_upload):
        mock_result = {"secure_url": "https://cloudinary.com/sample_image.jpg"}
        mock_upload.return_value = mock_result
        file = UploadFile(filename="avatar.jpg", file=BytesIO(b"sample image content"))
        user_repo = UserRepository(self.mock_session) 
        result = await user_repo.upload_to_cloudinary(file)
        self.assertEqual(result, "https://cloudinary.com/sample_image.jpg")
        mock_upload.assert_called_once_with(file.file)

    @patch("cloudinary.uploader.upload")
    async def test_upload_to_cloudinary_failure(self, mock_upload):
        mock_upload.side_effect = Exception("Failed to upload avatar")
        file = UploadFile(filename="avatar.jpg", file=BytesIO(b"sample image content"))
        user_repo = UserRepository(self.mock_session)
        with self.assertRaises(HTTPException) as context:
            await user_repo.upload_to_cloudinary(file)
        self.assertEqual(context.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Failed to upload avatar", str(context.exception))
        mock_upload.assert_called_once_with(file.file)

    @patch("src.auth.repos.UserRepository.get_user_by_email")
    async def test_update_avatar(self, MockGetUserByEmail):
        mock_user = User(
            username="testuser", 
            email="test@example.com", 
            avatar_url="old_avatar_url",
        )
        MockGetUserByEmail.return_value = mock_user
        new_avatar_url = "new_avatar_url"
        updated_user = await self.user_repo.update_avatar("test@example.com", new_avatar_url)
        self.assertEqual(updated_user.avatar_url, new_avatar_url)
        self.mock_session.commit.assert_called_once()
        self.mock_session.add.assert_called_once_with(updated_user)

    @patch("src.auth.repos.UserRepository.get_user_by_email")
    async def test_activate_user(self, MockGetUserByEmail):
        mock_user = User(username="testuser", email="test@example.com", is_active=False)
        MockGetUserByEmail.return_value = mock_user
        await self.user_repo.activate_user(mock_user)
        assert mock_user.is_active is True
        self.mock_session.add.assert_called_once_with(mock_user)
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once_with(mock_user)

    @patch("src.auth.repos.UserRepository.get_user_by_email")
    async def test_update_user_password(self, MockGetUserByEmail):
        mock_user = User(username="testuser", email="test@example.com", hashed_password="old_hashed_password")
        MockGetUserByEmail.return_value = mock_user
        new_hashed_password = "new_hashed_password"
        await self.user_repo.update_user_password(mock_user, new_hashed_password)
        self.assertEqual(mock_user.hashed_password, new_hashed_password)
        self.mock_session.commit.assert_called_once()
        self.mock_session.add.assert_not_called()


class TestRoleRepository(unittest.IsolatedAsyncioTestCase):

    @patch("src.auth.repos.AsyncSession")  
    async def test_get_role_by_name(self, MockSession):
        mock_session_instance = MockSession.return_value.__aenter__.return_value
        mock_session_instance.execute = AsyncMock()
        mock_role = Role(name=RoleEnum.ADMIN)
        mock_session_instance.execute.return_value.scalar_one_or_none = MagicMock(return_value = mock_role)
        role_repo = RoleRepository(session=mock_session_instance)
        result = await role_repo.get_role_by_name(RoleEnum.ADMIN)
        self.assertEqual(result, mock_role)
        mock_session_instance.execute.assert_called_once()

    @patch("src.auth.repos.AsyncSession") 
    async def test_get_role_by_name_not_found(self, MockSession):
        mock_session_instance = MockSession.return_value.__aenter__.return_value
        mock_session_instance.execute = AsyncMock()
        mock_session_instance.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)
        role_repo = RoleRepository(session=mock_session_instance)
        result = await role_repo.get_role_by_name(RoleEnum.ADMIN)
        self.assertIsNone(result)
        mock_session_instance.execute.assert_called_once()