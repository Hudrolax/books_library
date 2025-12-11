from abc import ABC, abstractmethod
from typing import List, Protocol

from ..interfaces.mixins_repo_iface import (
    IList,
    IRead,
)
from ..models.base_domain_model import TDomain
from ..models.book import Book, BookDict, BookFields


class IBookRepoProtocol(
    IRead[TDomain, BookDict],
    IList[TDomain, BookDict, BookFields],
    Protocol,
): ...


class IBookService(ABC):
    @abstractmethod
    async def read(self, filters: BookDict) -> Book: ...

    @abstractmethod
    async def list(self, filters: BookDict) -> List[Book]: ...

    @abstractmethod
    async def search(self, query: str) -> List[Book]: ...
