from typing import Literal

from pydantic import Field

from .base_domain_model import BaseCreateDict, BaseDomainModel


class User(BaseDomainModel):
    id: int = Field(..., description='ID в БД')
    username: str = Field(..., description='username пользователя')
    hashed_password: str | None = Field(None, description='Хеш пароля')
    telegram_id: int | None = Field(None, description='Telegram ID')
    level: int = Field(0, description='Уровень доступа') 


class UserDict(BaseCreateDict, total=False):
    id: int
    username: str
    hashed_password: str | None
    telegram_id: int | None
    level: int


UserFields = Literal["id", "username", "hashed_password", "telegram_id", "level"]
