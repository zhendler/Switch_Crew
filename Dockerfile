FROM python:3.12-slim
LABEL authors="Switch_Crew"
# Встановлюємо Poetry
RUN pip install --upgrade pip && pip install poetry
# Копіюємо файли залежностей і налаштування
WORKDIR /app
COPY poetry.lock pyproject.toml README.md ./
# Налаштовуємо Poetry і встановлюємо залежності
RUN poetry config virtualenvs.create false \
    && poetry install --no-root
# Копіюємо решту проєкту
COPY . .
# Відкриваємо порт
EXPOSE 8000
# Запускаємо додаток
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]