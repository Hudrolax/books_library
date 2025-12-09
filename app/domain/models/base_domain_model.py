from abc import ABC
from typing import TypedDict, TypeVar

from pydantic import BaseModel, ConfigDict


class BaseDomainModel(BaseModel, ABC):
    model_config = ConfigDict(from_attributes=True)


class BaseCreateDict(TypedDict):
    """Базовый TypedDict для привязки BaseCreateDict через bound."""
    ...


TDomain = TypeVar("TDomain", bound=BaseDomainModel)
TCovDomain = TypeVar("TCovDomain", bound=BaseDomainModel, covariant=True)

TTypedDict = TypeVar("TTypedDict", bound=BaseCreateDict, contravariant=True)

TDictFields = TypeVar("TDictFields")
