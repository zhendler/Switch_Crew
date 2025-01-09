FROM python:3.12-slim

LABEL authors="Switch_Crew"

# Устанавливаем Poetry
RUN pip install --upgrade pip && pip install poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только файлы зависимостей для установки
COPY poetry.lock pyproject.toml ./

# Конфигурируем Poetry для использования виртуального окружения внутри контейнера
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-root

# Копируем остальной проект
COPY . .

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
