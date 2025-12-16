from fastapi import FastAPI
from app.api.v1.auth import auth

app = FastAPI(
    title="TargetLayer API",
    description="Сервис декомпозиции целей с ИИ и авторизацией",
    version="0.1.0"
)

app.include_router(auth.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "TargetLayer API is running!"}