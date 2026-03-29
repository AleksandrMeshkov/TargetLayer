from pydantic import BaseModel, EmailStr

from app.schemas.password_common import PasswordInput, StrongPassword

class UserRegister(BaseModel):
    email: EmailStr
    password: StrongPassword
    name: str
    surname: str
    patronymic: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: PasswordInput

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"