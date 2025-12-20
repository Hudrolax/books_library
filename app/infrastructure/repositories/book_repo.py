import asyncio
from typing import Any, Generic

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from config.config import settings
from domain.exceptions import RepositoryException
from domain.models.base_domain_model import TDomain, TTypedDict
from domain.models.book import BookDict, BookFields
from infrastructure.search.books_index import build_books_search_query, ensure_books_index
from infrastructure.search.es_client import elasticsearch_enabled, get_elasticsearch

from ..db.models.base_model_orm import TOrm
from .sqlalchemy_mixins import ListMixin, ReadMixin


class BookRepo(
    ReadMixin[TDomain, TOrm, BookDict],
    ListMixin[TDomain, TOrm, BookDict, BookFields],
    Generic[TDomain, TOrm, TTypedDict],
):
    async def search(
        self,
        *,
        q: str | None = None,
        author: str | None = None,
        title: str | None = None,
        limit: int | None = None,
    ) -> list[TDomain]:
        try:
            if not elasticsearch_enabled():
                raise RepositoryException(
                    "Поиск недоступен: не задан ELASTICSEARCH_URL (или он пуст). "
                    "Подними Elasticsearch и задай переменную окружения."
                )

            await ensure_books_index(self.db)
            client = get_elasticsearch()

            query = build_books_search_query(q=q, author=author, title=title)
            resp: dict[str, Any] = await asyncio.to_thread(
                client.search,
                index=settings.ELASTICSEARCH_INDEX,
                body={"query": query, "size": limit or 50, "_source": False},
            )
            hits = resp.get("hits", {}).get("hits", [])
            ids = [int(hit["_id"]) for hit in hits if "_id" in hit]
            if not ids:
                return []

            # Тянем полные книги из БД по id и сохраняем порядок релевантности из Elasticsearch.
            rows = (await self.db.execute(select(self.orm_class).where(self.orm_class.id.in_(ids)))).scalars().all()
            by_id = {row.id: row for row in rows}
            ordered = [by_id[i] for i in ids if i in by_id]
            return [self.domain_model.model_validate(row) for row in ordered]
        except SQLAlchemyError as ex:
            raise RepositoryException(str(ex))
        except Exception as ex:  # noqa: BLE001
            raise RepositoryException(f"Ошибка поиска в Elasticsearch: {ex}") from ex
