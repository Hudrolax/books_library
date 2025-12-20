import asyncio

from elasticsearch import Elasticsearch

from config.config import settings


_client: Elasticsearch | None = None


def elasticsearch_enabled() -> bool:
    return bool(settings.ELASTICSEARCH_URL and settings.ELASTICSEARCH_URL.strip())


async def init_elasticsearch() -> None:
    global _client
    if _client is not None:
        return
    if not elasticsearch_enabled():
        return

    # Sync-клиент безопаснее в окружениях, где event loop может меняться (pytest/anyio).
    # Все вызовы к клиенту выполняются через asyncio.to_thread.
    _client = Elasticsearch(
        hosts=[settings.ELASTICSEARCH_URL],
        request_timeout=settings.ELASTICSEARCH_REQUEST_TIMEOUT_S,
    )


async def close_elasticsearch() -> None:
    global _client
    if _client is None:
        return
    await asyncio.to_thread(_client.close)
    _client = None


def get_elasticsearch() -> Elasticsearch:
    if not elasticsearch_enabled():
        raise RuntimeError("Elasticsearch выключен: ELASTICSEARCH_URL не задан (или пуст).")
    if _client is None:
        raise RuntimeError(
            "Elasticsearch client не инициализирован. "
            "Проверь, что приложение стартует с lifespan (init_elasticsearch)."
        )
    return _client
