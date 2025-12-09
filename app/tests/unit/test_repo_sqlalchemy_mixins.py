from typing import Literal, TypedDict, cast

import pytest
from conftest import Base
from sqlalchemy import Integer, String, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from domain.exceptions import DoubleFoundError, NotFoundError
from domain.models.base_domain_model import BaseDomainModel
from infrastructure.repositories.sqlalchemy_mixins import (
    CountMixin,
    CreateMixin,
    DeleteMixin,
    ExistsMixin,
    ListMixin,
    ReadMixin,
    UpdateMixin,
)


# Определяем фиктивную ORM-модель, используя Base из conftest.py,
# чтобы таблица создавалась автоматически в in-memory БД.
class DummyORM(Base):
    __tablename__ = "dummy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)


# Фиктивная доменная модель с методом model_validate, используемая миксинами.
class DummyDomain(BaseDomainModel):
    id: int
    name: str


class DummyTyped(TypedDict, total=False):
    id: int
    name: str | list[str]


DummyFields = Literal["id", "name"]


# Создаем репозиторий, комбинирующий все миксины.
class DummyRepo(
    CreateMixin[DummyDomain, DummyORM, DummyTyped],
    ReadMixin[DummyDomain, DummyORM, DummyTyped],
    ListMixin[DummyDomain, DummyORM, DummyTyped, DummyFields],
    UpdateMixin[DummyDomain, DummyORM, DummyTyped],
    DeleteMixin[DummyDomain, DummyORM, DummyTyped],
    CountMixin[DummyDomain, DummyORM, DummyTyped],
    ExistsMixin[DummyDomain, DummyORM, DummyTyped],
):
    def __init__(self, db: AsyncSession):
        super().__init__(db, DummyDomain, DummyORM)


# Вспомогательная функция для очистки таблицы перед каждым тестом.
async def clear_table(session: AsyncSession):
    await session.execute(delete(DummyORM))
    await session.commit()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create(async_session: AsyncSession):
    await clear_table(async_session)
    repo = DummyRepo(async_session)
    domain_obj = await repo.create({"name": "test_create"})
    assert domain_obj.name == "test_create"

    # Проверка через прямой запрос к базе
    result = await async_session.execute(select(DummyORM).where(DummyORM.name == "test_create"))
    orm_obj = result.scalar_one()
    assert orm_obj.name == "test_create"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_read(async_session: AsyncSession):
    await clear_table(async_session)
    repo = DummyRepo(async_session)

    # Создаем запись и затем читаем её
    await repo.create({"name": "test_read"})
    read_obj = await repo.read(filters={"name": "test_read"})
    assert read_obj.name == "test_read"

    # Если запись не найдена, должно выброситься исключение NotFoundError
    with pytest.raises(NotFoundError):
        await repo.read(filters={"name": "nonexistent"})

    # Проверка DoubleFoundError — создаем две записи с одинаковым именем
    await repo.create({"name": "duplicate"})
    await repo.create({"name": "duplicate"})
    with pytest.raises(DoubleFoundError):
        await repo.read(filters={"name": "duplicate"})


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_with_sorting_and_or_filters(async_session: AsyncSession):
    # Очистка таблицы перед тестом
    await clear_table(async_session)

    repo = DummyRepo(async_session)

    # Создаем записи с именами
    names = ["Alice", "Bob", "Charlie"]
    for name in names:
        await repo.create({"name": name})

    # Проверяем сортировку: без фильтров получаем все записи, упорядоченные по имени
    domain_list = await repo.list(filters={}, order_columns=[cast(DummyFields, DummyORM.name)])
    listed_names = [d.name for d in domain_list]
    assert listed_names == sorted(names)

    # Проверяем фильтрацию с OR-условием: передаём список значений для поля name
    # Ожидаем, что будут возвращены записи, у которых name равен "Alice" или "Charlie"
    filtered_list = await repo.list(
        filters={"name": ["Alice", "Charlie"]}, order_columns=[cast(DummyFields, DummyORM.name)]
    )
    filtered_names = [d.name for d in filtered_list]
    # Порядок также определяется order_columns, поэтому ожидаем отсортированный список
    assert filtered_names == sorted(["Alice", "Charlie"])


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update(async_session: AsyncSession):
    await clear_table(async_session)
    repo = DummyRepo(async_session)
    # Создаем запись
    domain_obj = await repo.create({"name": "old_name"})
    # Обновляем запись
    updated_objs = await repo.update({"name": "new_name"}, filters={"id": domain_obj.id})
    assert len(updated_objs) == 1
    assert updated_objs[0].name == "new_name"

    # Проверяем, что обновление применилось (чтением из базы)
    read_obj = await repo.read(filters={"id": domain_obj.id})
    assert read_obj.name == "new_name"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete(async_session: AsyncSession):
    await clear_table(async_session)
    repo = DummyRepo(async_session)
    # Создаем две записи
    await repo.create({"name": "to_delete"})
    await repo.create({"name": "to_keep"})

    # Удаляем запись с именем "to_delete"
    deleted_count = await repo.delete(filters={"name": "to_delete"})
    assert deleted_count == 1

    # Проверяем, что удаленная запись не находится
    with pytest.raises(NotFoundError):
        await repo.read(filters={"name": "to_delete"})

    # Остальная запись должна присутствовать
    remaining_obj = await repo.read(filters={"name": "to_keep"})
    assert remaining_obj.name == "to_keep"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_count(async_session: AsyncSession):
    await clear_table(async_session)
    repo = DummyRepo(async_session)

    # Создаем запись и затем читаем её
    await repo.create({"name": "first"})
    await repo.create({"name": "second"})
    count = await repo.count(filters={"name": "first"})
    assert count == 1

    count_zero = await repo.count(filters={"name": "nonexistent"})
    assert count_zero == 0

    count2 = await repo.count()
    assert count2 == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_exists(async_session: AsyncSession):
    await clear_table(async_session)
    repo = DummyRepo(async_session)
    await repo.create({"name": "test"})

    exists = await repo.exists(filters={"name": "fake_user"})
    assert exists is False
    exists = await repo.exists(filters={"name": "test"})
    assert exists is True
