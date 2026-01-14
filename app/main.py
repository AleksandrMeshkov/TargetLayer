from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.v1.auth import auth
from app.api.v1.verify import verify
from app.api.v1.ai import ai_routes
from app.api.v1.user_settings import user_settings

app = FastAPI(
    title="TargetLayer API",
    description="Сервис декомпозиции целей с ИИ",
    version="0.1.0"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="TargetLayer API",
        version="0.1.0",
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
app.include_router(verify.router)
app.include_router(ai_routes.router)
app.include_router(user_settings.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "TargetLayer API is running!"}