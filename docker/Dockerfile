FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install --no-cache-dir poetry

# Отключение создания виртуального окружения в Poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PYTHONUNBUFFERED=1

# Копирование файлов зависимостей
COPY pyproject.toml ./

# Обновление lock файла и установка зависимостей
RUN poetry lock && poetry install --only main --no-root

# Копирование приложения
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Здоровье-проверка
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Запуск миграций и приложения
CMD ["sh", "-c", "poetry run alembic upgrade head && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
