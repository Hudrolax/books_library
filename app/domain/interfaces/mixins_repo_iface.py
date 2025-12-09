from typing import Generic, Optional, Protocol

from ..models.base_domain_model import TCovDomain, TDictFields, TDomain, TTypedDict


class ICreate(Protocol, Generic[TCovDomain, TTypedDict]):
    async def create(self, data: TTypedDict) -> TCovDomain: ...


class IRead(Protocol, Generic[TCovDomain, TTypedDict]):
    async def read(self, filters: Optional[TTypedDict] = None) -> TCovDomain: ...


class IList(Protocol, Generic[TDomain, TTypedDict, TDictFields]):
    async def list(
        self,
        filters: Optional[TTypedDict] = None,
        order_columns: Optional[list[TDictFields]] = None,
    ) -> list[TDomain]: ...


class IUpdate(Protocol, Generic[TDomain, TTypedDict]):
    async def update(self, data: TTypedDict, filters: Optional[TTypedDict] = None) -> list[TDomain]: ...


class IDelete(Protocol, Generic[TTypedDict]):
    async def delete(self, filters: TTypedDict) -> int: ...


class ICount(Protocol, Generic[TTypedDict]):
    async def count(self, filters: Optional[TTypedDict] = None) -> int: ...


class IExists(Protocol, Generic[TTypedDict]):
    async def exists(self, filters: Optional[TTypedDict] = None) -> bool: ...


class IVectorSearch(Protocol, Generic[TDomain, TTypedDict]):
    async def list_by_embedding(
        self,
        embedding: list[float],
        limit: int,
        filters: Optional[TTypedDict] = None,
    ) -> list[TDomain]: ...
