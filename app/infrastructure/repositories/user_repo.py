from typing import Generic

from domain.models.base_domain_model import TDomain, TTypedDict
from domain.models.user import UserDict, UserFields

from ..db.models.base_model_orm import TOrm
from .sqlalchemy_mixins import CreateMixin, ExistsMixin, ListMixin, ReadMixin, UpdateMixin


class UserRepo(
    CreateMixin[TDomain, TOrm, UserDict],
    ReadMixin[TDomain, TOrm, UserDict],
    UpdateMixin[TDomain, TOrm, UserDict],
    ListMixin[TDomain, TOrm, UserDict, UserFields],
    ExistsMixin[TDomain, TOrm, UserDict],
    Generic[TDomain, TOrm, TTypedDict],
): ...
