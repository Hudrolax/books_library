from sqlalchemy import BIGINT, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base_model_orm import BaseORMModel


class UserORM(BaseORMModel):
    """ORM-таблица пользователей."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    telegram_id: Mapped[int] = mapped_column(BIGINT, unique=True, index=True, nullable=True)
    level: Mapped[int] = mapped_column(Integer, index=True, nullable=False, default=0) # Уровень доступа
