from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.password_common import PasswordInput, StrongPassword

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: StrongPassword
    name: str = Field(min_length=1, max_length=100)
    surname: str = Field(min_length=1, max_length=100)
    patronymic: str | None = Field(default=None, max_length=100)

    @field_validator("username", "name", "surname", mode="before")
    @classmethod
    def validate_required_text_fields(cls, value: str) -> str:
        if value is None:
            raise ValueError("Field is required")
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Field must not be empty")
        return normalized

    @field_validator("patronymic", mode="before")
    @classmethod
    def normalize_patronymic(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class UserLogin(BaseModel):
    email: EmailStr
    password: PasswordInput

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"