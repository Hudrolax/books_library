import asyncio
from typing import Any

from elasticsearch.helpers import bulk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from infrastructure.db.models.book_orm import BookORM

from .es_client import get_elasticsearch


_index_lock = asyncio.Lock()


def build_books_search_query(*, q: str | None, author: str | None, title: str | None) -> dict[str, Any]:
    """
    Строит Query DSL для поиска книг (as-you-type + русская нормализация).

    Требования (поведение, близкое к прежнему FTS5):
    - поддержка префиксного поиска по термам (type-ahead);
    - AND-логика по словам внутри одного параметра;
    - возможность комбинировать author/title/q.
    """

    def _bool_prefix(fields: list[str], query: str) -> dict[str, Any]:
        return {
            "multi_match": {
                "query": query,
                "type": "bool_prefix",
                "fields": fields,
                "operator": "and",
            }
        }

    must: list[dict[str, Any]] = []

    if q:
        must.append(
            _bool_prefix(
                [
                    "title",
                    "title._2gram",
                    "title._3gram",
                    "author",
                    "author._2gram",
                    "author._3gram",
                ],
                q,
            )
        )
    if author:
        must.append(_bool_prefix(["author", "author._2gram", "author._3gram"], author))
    if title:
        must.append(_bool_prefix(["title", "title._2gram", "title._3gram"], title))

    return {"bool": {"must": must}} if must else {"match_none": {}}


def _books_index_body() -> dict[str, Any]:
    # Минимальные настройки под single-node (dev/tests).
    # В проде можно переопределять через отдельный индекс/темплейт.
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "char_filter": {
                    "yo_mapping": {
                        "type": "mapping",
                        "mappings": [
                            "ё=>е",
                            "Ё=>Е",
                        ],
                    }
                },
                "filter": {
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "russian_stemmer": {"type": "stemmer", "language": "russian"},
                },
                "analyzer": {
                    "ru_text": {
                        "type": "custom",
                        "char_filter": ["yo_mapping"],
                        "tokenizer": "standard",
                        "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                    }
                },
            },
        },
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "author": {"type": "search_as_you_type", "analyzer": "ru_text"},
                "title": {"type": "search_as_you_type", "analyzer": "ru_text"},
            }
        },
    }


async def ensure_books_index(session: AsyncSession) -> None:
    """
    Создаёт индекс книг при необходимости и (опционально) индексирует данные из БД, если индекс пуст.

    Важно: индексирование происходит из переданной SQLAlchemy-сессии, чтобы в тестах
    работала in-memory БД через dependency override.
    """
    if not settings.ELASTICSEARCH_URL:
        return

    client = get_elasticsearch()
    index = settings.ELASTICSEARCH_INDEX

    async with _index_lock:
        exists = await asyncio.to_thread(client.indices.exists, index=index)
        if not exists:
            await asyncio.to_thread(client.indices.create, index=index, body=_books_index_body())

        if not settings.ELASTICSEARCH_AUTO_INDEX:
            return

        try:
            count_resp = await asyncio.to_thread(client.count, index=index)
            docs_count = int(count_resp.get("count", 0))
        except Exception:  # noqa: BLE001
            # Если count упал (например, из-за race/cluster state), не пытаемся автоиндексировать.
            return

        if docs_count > 0:
            return

        stmt = select(BookORM.id, BookORM.author, BookORM.title)
        result = await session.stream(stmt)

        batch: list[dict[str, Any]] = []
        async for row in result:
            batch.append(
                {
                    "_op_type": "index",
                    "_index": index,
                    "_id": str(row.id),
                    "_source": {
                        "id": int(row.id),
                        "author": row.author or "",
                        "title": row.title or "",
                    },
                }
            )
            if len(batch) >= 500:
                await asyncio.to_thread(bulk, client, batch, refresh=False)
                batch.clear()

        if batch:
            await asyncio.to_thread(bulk, client, batch, refresh=False)

        await asyncio.to_thread(client.indices.refresh, index=index)


async def delete_books_index_if_exists() -> None:
    if not settings.ELASTICSEARCH_URL:
        return
    client = get_elasticsearch()
    index = settings.ELASTICSEARCH_INDEX
    if await asyncio.to_thread(client.indices.exists, index=index):
        await asyncio.to_thread(client.indices.delete, index=index)
