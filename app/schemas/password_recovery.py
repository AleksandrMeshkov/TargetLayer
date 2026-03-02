from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class PasswordRecoveryRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="Email адрес пользователя")


class PasswordRecoveryConfirmSchema(BaseModel):
    
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Новый пароль"
    )
    confirm_password: str = Field(
        ...,
        description="Подтверждение нового пароля"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        
        if not any(c.islower() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)')
        
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Пароли не совпадают')
        return v


class PasswordRecoveryResponseSchema(BaseModel):
    status: str = Field("success", description="Статус операции")
    message: str = Field(..., description="Сообщение для пользователя")
    email: str = Field(..., description="Email на который отправлено письмо")
