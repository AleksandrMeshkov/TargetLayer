from fastapi import FastAPI
from app.api.v1 import auth

app = FastAPI(title="TargetLayer API")

app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "TargetLayer API is running!"}