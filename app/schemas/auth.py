from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    surname: str
    patronymic: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"