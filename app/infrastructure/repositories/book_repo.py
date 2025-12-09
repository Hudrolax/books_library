from typing import Generic

from domain.models.base_domain_model import TDomain, TTypedDict
from domain.models.book import BookDict, BookFields

from ..db.models.base_model_orm import TOrm
from .sqlalchemy_mixins import ListMixin, ReadMixin


class BookRepo(
    ReadMixin[TDomain, TOrm, BookDict],
    ListMixin[TDomain, TOrm, BookDict, BookFields],
    Generic[TDomain, TOrm, TTypedDict],
): ...
