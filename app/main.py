from fastapi import FastAPI
from app.api.v1.auth import auth
from app.api.v1.verify import verify
from app.api.v1.ai import ai_routes

app = FastAPI(
    title="TargetLayer API",
    description="Сервис декомпозиции целей с ИИ и авторизацией",
    version="0.1.0"
)

app.include_router(auth.router)
app.include_router(verify.router)
app.include_router(ai_routes.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "TargetLayer API is running!"}