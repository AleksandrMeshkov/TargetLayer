from fastapi import FastAPI
from app.api.v1.auth import auth  # ← импортируем модуль auth

# Создаём приложение
app = FastAPI(
    title="TargetLayer API",
    description="Сервис декомпозиции целей с ИИ и авторизацией",
    version="0.1.0"
)

# Подключаем роутеры из auth.py
app.include_router(auth.router)

# Корневой эндпоинт для проверки работоспособности
@app.get("/", tags=["Root"])
async def root():
    return {"message": "TargetLayer API is running!"}