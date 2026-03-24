from pydantic import BaseModel, EmailStr, Field

from app.schemas.password_common import PasswordWithConfirmationSchema


class PasswordRecoveryRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="Email адрес пользователя")


class PasswordRecoveryConfirmSchema(PasswordWithConfirmationSchema):
    pass


class PasswordRecoveryResponseSchema(BaseModel):
    status: str = Field("success", description="Статус операции")
    message: str = Field(..., description="Сообщение для пользователя")
    email: str = Field(..., description="Email на который отправлено письмо")
