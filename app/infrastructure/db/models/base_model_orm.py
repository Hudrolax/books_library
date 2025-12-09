from typing import TypeVar

from ..db import Base


class BaseORMModel(Base):
    __abstract__ = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "__tablename__" not in cls.__dict__:
            raise NotImplementedError(f"class {cls.__name__} must have __tablename__ attribute")


TOrm = TypeVar("TOrm", bound=BaseORMModel)
