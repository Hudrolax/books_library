from typing import Generic, Optional, Type, cast

from sqlalchemy import insert, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions import DoubleFoundError, NotFoundError, RepositoryException
from domain.models.base_domain_model import TDictFields, TDomain, TTypedDict

from ..db.models.base_model_orm import TOrm


class BaseSQLAlchemyRepo(Generic[TDomain, TOrm]):
    def __init__(
        self,
        db: AsyncSession,
        domain_model: Type[TDomain],
        orm_class: Type[TOrm],
    ) -> None:
        self.db: AsyncSession = db
        self.domain_model = domain_model
        self.orm_class = orm_class


class CreateMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict]):
    async def create(self, data: TTypedDict) -> TDomain:
        stmt = insert(self.orm_class).values(**data).returning(self.orm_class)
        try:
            result = await self.db.execute(stmt)
        except IntegrityError as ex:
            # Проверяем, что это именно нарушение уникального ограничения
            orig = ex.orig
            pgcode = getattr(orig, "pgcode", None)
            msg = str(orig).lower()

            is_pg_unique_violation = pgcode == "23505"
            is_sqlite_unique_violation = "unique constraint failed" in msg
            is_mysql_duplicate_key = "duplicate entry" in msg

            if is_pg_unique_violation or is_sqlite_unique_violation or is_mysql_duplicate_key:
                await self.db.rollback()
                raise DoubleFoundError("Запись с такими данными уже существует") from ex

            raise
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))

        row = result.scalar_one()
        return self.domain_model.model_validate(row)


class ReadMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict]):
    async def read(self, filters: Optional[TTypedDict] = None) -> TDomain:
        stmt = select(self.orm_class)
        if filters:
            stmt = stmt.filter_by(**filters)
        try:
            res = (await self.db.execute(stmt)).scalars().all()
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))

        if not res:
            raise NotFoundError
        elif len(res) > 1:
            raise DoubleFoundError

        return self.domain_model.model_validate(res[0])


class ListMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict, TDictFields]):
    async def list(
        self,
        filters: Optional[TTypedDict] = None,
        order_columns: Optional[list[TDictFields]] = None,
    ) -> list[TDomain]:
        stmt = select(self.orm_class)
        if filters:
            conditions = []
            for key, value in filters.items():
                column = getattr(self.orm_class, key)
                if isinstance(value, list):
                    # Создаем условие: column == value1 OR column == value2 OR ...
                    conditions.append(or_(*[column == item for item in value]))
                else:
                    conditions.append(column == value)
            stmt = stmt.filter(*conditions)
        if order_columns:
            stmt = stmt.order_by(*(cast(list[str], order_columns)))
        try:
            result = await self.db.execute(stmt)
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))
        rows = result.scalars().all()
        return [self.domain_model.model_validate(row) for row in rows]


class UpdateMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict]):
    async def update(self, data: TTypedDict, filters: Optional[TTypedDict] = None) -> list[TDomain]:
        stmt = select(self.orm_class)
        if filters:
            stmt = stmt.filter_by(**filters)
        try:
            records = (await self.db.execute(stmt)).scalars().all()
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))
        if not records:
            return []

        updated_records = []
        for record in records:
            for key, value in data.items():
                setattr(record, key, value)
            updated_records.append(self.domain_model.model_validate(record))

        return updated_records


class DeleteMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict]):
    async def delete(self, filters: TTypedDict) -> int:
        stmt = select(self.orm_class)
        if filters:
            stmt = stmt.filter_by(**filters)
        try:
            records = (await self.db.execute(stmt)).scalars().all()
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))

        if not records:
            return 0

        for record in records:
            await self.db.delete(record)

        return len(records)


class CountMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict]):
    async def count(self, filters: Optional[TTypedDict] = None) -> int:
        stmt = select(self.orm_class)
        if filters:
            stmt = stmt.filter_by(**filters)
        try:
            res = (await self.db.execute(stmt)).scalars().all()
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))

        return len(res)


class ExistsMixin(BaseSQLAlchemyRepo[TDomain, TOrm], Generic[TDomain, TOrm, TTypedDict]):
    async def exists(self, filters: Optional[TTypedDict] = None) -> bool:
        stmt = select(self.orm_class)
        if filters:
            stmt = stmt.filter_by(**filters)
        try:
            res = (await self.db.execute(stmt)).scalars().all()
            return len(res) > 0
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))


class VectorSearchMixin(
    BaseSQLAlchemyRepo[TDomain, TOrm],
    Generic[TDomain, TOrm, TTypedDict],
):
    async def list_by_embedding(
        self,
        embedding: list[float],
        limit: int,
        filters: Optional[TTypedDict] = None,
    ) -> list[TDomain]:
        # 1. Базовый select
        stmt = select(self.orm_class)

        # 2. Применяем фильтры, если есть
        if filters:
            conditions = []
            for key, value in filters.items():
                column = getattr(self.orm_class, key)
                if isinstance(value, list):
                    # column == v1 OR column == v2 OR …
                    conditions.append(or_(*[column == item for item in value]))
                else:
                    conditions.append(column == value)
            stmt = stmt.filter(*conditions)

        # 3. Сортируем по косинусному расстоянию и ограничиваем
        stmt = stmt.order_by(self.orm_class.vector.op("<=>")(embedding)).limit(limit)

        # 4. Выполняем и мапим результат
        try:
            result = await self.db.execute(stmt)
        except SQLAlchemyError as ex:
            raise RepositoryException(f"Vector search error: {ex}")

        rows = result.scalars().all()
        return [self.domain_model.model_validate(row) for row in rows]
