import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, model_validator

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
SPECIAL_SYMBOL_PATTERN = r'[!@#$%^&*(),.?":{}|<>]'


def validate_password_strength(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError("Пароль должен содержать минимум 8 символов")

    if not any(char.isupper() for char in value):
        raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")

    if not any(char.islower() for char in value):
        raise ValueError("Пароль должен содержать хотя бы одну строчную букву")

    if not any(char.isdigit() for char in value):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")

    if not re.search(SPECIAL_SYMBOL_PATTERN, value):
        raise ValueError("Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)")

    return value


PasswordInput = Annotated[
    str,
    Field(min_length=1, max_length=MAX_PASSWORD_LENGTH, description="Пароль"),
]

StrongPassword = Annotated[
    str,
    Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH, description="Пароль"),
    AfterValidator(validate_password_strength),
]


class PasswordWithConfirmationSchema(BaseModel):
    old_password: PasswordInput = Field(..., description="Текущий пароль")
    new_password: StrongPassword = Field(..., description="Новый пароль")
    confirm_password: str = Field(..., min_length=1, description="Подтверждение нового пароля")

    @model_validator(mode="after")
    def passwords_match(self):
        if self.confirm_password != self.new_password:
            raise ValueError("Пароли не совпадают")
        return self
