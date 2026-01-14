from pydantic import BaseModel, Field, EmailStr, HttpUrl, Field
from typing import Optional
from datetime import datetime

class UserNameSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    surname: str = Field(..., min_length=1, max_length=100, description="Фамилия пользователя")
    patronymic: Optional[str] = Field(None, max_length=100, description="Отчество пользователя")
    

class UserAvatarSchema(BaseModel):
    avatar_url: Optional[str] = Field(
        None, 
        max_length=255, 
        description="URL аватара пользователя"
    )

