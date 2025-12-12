from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    surname: str
    patronymic: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"