import unittest
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, Mock
from main import app
from src.models.models import Tag, Photo
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

client = TestClient(app)

class TestTagsRouter(unittest.TestCase):


    @patch('src.tags.repos.TagRepository.get_all_tags', return_value=[Tag(id=1, name='tag1'), Tag(id=2, name='tag2')])
    def test_get_all_tags(self, mock_get_all_tags):
        response = client.get("/tags/")

        assert response.status_code == 200

        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["name"] == "tag1"
        assert response_data[1]["name"] == "tag2"

        mock_get_all_tags.assert_called_once()

    @patch('src.tags.repos.TagRepository')
    @patch("config.db.get_db", new_callable=AsyncMock)
    async def test_create_tag(self, mock_get_db, MockTagRepository):
        # Мокируем базу данных
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db

        # Создаем мок репозитория
        tag_repo = MockTagRepository(mock_db)
        tag_repo.create_tag = AsyncMock()
        tag_repo.get_tag_by_name = AsyncMock(return_value=None)


        with TestClient(app) as client:
            # Авторизация и получение токена
            form_data = {"username": "user5", "password": "user5"}
            auth_response = client.post("/auth/token", data=form_data)
            assert auth_response.status_code == 200
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Тест создания тега
            tag_data = {"tag_name": "New Tag"}
            response = client.post("/tags/create/", data=tag_data, headers=headers)

            # Проверяем статус ответа
            assert response.status_code == 201

            # Проверяем данные ответа
            response_data = response.json()
            print(response_data)
            assert response_data["name"] == "New Tag"
            mock_db.add.assert_not_called()
            mock_db.commit.assert_not_called()
            print('1111111111111111111111111111111111111111')
            mock_db.refresh.assert_not_called()


    @patch('src.tags.repos.TagRepository')
    @patch("config.db.get_db", new_callable=AsyncMock)
    async def test_create_tag2(self, mock_get_db, MockTagRepository):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db

        tag_repo = MockTagRepository(mock_db)
        tag_repo.create_tag = Mock()
        tag_repo.get_tag_by_name = AsyncMock(return_value=None)
        mock_create_tag = AsyncMock(return_value=Tag(name="New Tag", id=1))

        tag = await mock_create_tag("New Tag")
        assert tag.name == "New Tag"

        # Проверяем данные ответа
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()




    @patch('src.tags.repos.TagRepository.get_tag_by_name', return_value=Tag(id=1, name='tag1'))
    async def test_get_tag_by_name(self, mock_get_tag_by_name):
        response = client.get(f"/tags/tag1")

        assert response.status_code == 200

        response_data = response.json()
        assert len(response_data) == 2
        assert response_data["name"] == "tag1"

        mock_get_tag_by_name.assert_called_once()

    @patch('src.tags.repos.TagRepository.get_photos_by_tag',
           return_value=[Photo(id=1, url_link="existing_photo1", owner_id=1, tags=[Tag(id=1, name='existent_tag')]),
                         Photo(id=2, url_link="existing_photo2", owner_id=2, tags=[Tag(id=1, name='existent_tag'), Tag(id=2, name='existent_tag2')])])
    async def test_get_photos_by_tag(self, mock_get_photos_by_tag):
        response = client.get("/tags/existent_tag/photos/")
        response_data = response.json()

        assert response.status_code == 200
        assert len(response_data) == 2
        assert response_data[0]["url_link"] == "existing_photo1"
        assert response_data[0]["owner_id"] == 1
        assert response_data[1]["url_link"] == "existing_photo2"
        assert response_data[1]["id"] == 2

        mock_get_photos_by_tag.assert_called_once()

    # @patch('src.tags.repos.TagRepository')
    # async def test_delete_tag_by_name(self, MockTagRepository):
    #
    #     tag_repo = MockTagRepository.return_value
    #     tag_repo.delete_tag_by_name = AsyncMock()
    #     tag_repo.get_tag_by_name = AsyncMock(return_value=None)
    #
    #     response = client.delete(
    #         "/tags/create/",
    #         params={"tag_name": "New Tag"}
    #     )
    #
    #     assert response.status_code == 200
    #     tag_repo.delete_tag_by_name.assert_called_once_with(
    #         tag_name="New Tag")
    #     tag_repo.get_tag_by_name.assert_called_once_with(tag_name="New Tag")
    #
    # @patch('src.tags.repos.TagRepository')
    # async def test_update_tag_name(self, MockTagRepository):
    #     tag_repo = MockTagRepository.return_value
    #     tag_repo.update_tag_name = AsyncMock(return_value=Tag(name="updated_tag"))
    #     tag_repo.get_tag_by_name = AsyncMock(return_value=Tag(name="updated_tag"))
    #
    #     response = client.put(
    #         "/tags/update/tag-updated_tag"
    #     )
    #
    #     print(response.status_code)
    #     assert response.status_code == 200
    #     tag_repo.update_tag_name.assert_called_once_with("tag", "updated_tag")
    #     tag_repo.get_tag_by_name.assert_called_once_with(tag_name="updated_tag")


# @pytest.mark.asyncio
# @patch("config.db.get_db", new_callable=AsyncMock)
# @patch("src.tags.repos.TagRepository")
# async def test_create_tag(mock_tag_repository, mock_get_db):
#     # Настраиваем мок базы данных
#     mock_db_session = AsyncMock(spec=AsyncSession)
#     mock_get_db.return_value = mock_db_session
#
#     # Мок репозитория
#     mock_tag_repo_instance = mock_tag_repository.return_value
#     mock_tag_repo_instance.create_tag = AsyncMock()
#     mock_tag_repo_instance.get_tag_by_name = AsyncMock(return_value={"tag_name": "New Tag"})
#
#     # Используем TestClient для работы с приложением
#     client = TestClient(app)
#
#     # Авторизация и получение токена
#     form_data = {"username": "user5", "password": "user5"}
#     auth_response = client.post("/auth/token", data=form_data)
#     assert auth_response.status_code == status.HTTP_200_OK
#     token = auth_response.json()["access_token"]
#     headers = {"Authorization": f"Bearer {token}"}
#
#     # Тест создания тега
#     tag_data = {"tag_name": "New Tag"}
#     response = client.post("/tags/create/", data=tag_data, headers=headers)
#
#     # Проверяем статус ответа
#     assert response.status_code == status.HTTP_201_CREATED
#
#     # Проверяем данные ответа
#     response_data = response.json()
#     assert response_data["tag_name"] == "New Tag"
#
#     # Проверяем вызовы методов репозитория
#     mock_tag_repo_instance.create_tag.assert_called_once_with(tag_name="New Tag")
#     mock_tag_repo_instance.get_tag_by_name.assert_called_once_with(tag_name="New Tag")


if __name__ == "__main__":
    unittest.main()