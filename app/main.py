from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from app.api.v1.auth import auth, password_recovery
from app.api.v1.ai.ai_router import router as ai_router
from app.api.v1.user_settings import user_settings, update_password
from app.api.v1.roadmap import roadmap_router
from app.core.settings.cors import configure_cors
from app.core.settings.settings import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app")

app = FastAPI(
    title="TargetLayer API",
    description="Сервис декомпозиции целей с ИИ",
)
configure_cors(app)

settings.uploads_dir_path.mkdir(parents=True, exist_ok=True)
settings.avatars_dir_path.mkdir(parents=True, exist_ok=True)
app.mount(settings.UPLOADS_URL_PREFIX, StaticFiles(directory=str(settings.uploads_dir_path)), name="uploads")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="TargetLayer API",
        description="Сервис декомпозиции целей с ИИ",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT токен, полученный после логина"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(auth.router)
app.include_router(password_recovery.router)
app.include_router(ai_router)
app.include_router(user_settings.router)
app.include_router(update_password.router)
app.include_router(roadmap_router.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "TargetLayer API is running!"}