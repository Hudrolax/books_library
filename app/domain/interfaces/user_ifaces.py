from abc import ABC, abstractmethod
from typing import Optional, Protocol

from ..interfaces.mixins_repo_iface import (
    ICreate,
    IExists,
    IList,
    IRead,
    IUpdate,
)
from ..models.base_domain_model import TDomain
from ..models.user import User, UserDict, UserFields


class IUserRepoProtocol(
    ICreate[TDomain, UserDict],
    IRead[TDomain, UserDict],
    IUpdate[TDomain, UserDict],
    IList[TDomain, UserDict, UserFields],
    IExists[UserDict],
    Protocol,
): ...


class IUserService(ABC):
    @abstractmethod
    async def create(
        self,
        user: User,
        username: str,
        password: Optional[str] = None,
        telegram_id: Optional[int] = None,
        level: int = 0
    ) -> User: ...

    @abstractmethod
    async def read(self, filters: UserDict) -> User: ...

    @abstractmethod
    async def verify_password(self, username: str, password: str) -> User: ...

    @abstractmethod
    async def update_password(self, username: str, old_password: str, new_password: str) -> User: ...

    @abstractmethod
    async def update(self, user: User, id: int, data: UserDict) -> User: ...
