# Book Library

## MCP

Приложение поднимает MCP сервер FastMCP в том же ASGI-приложении, что и HTTP API.
При `API_ROOT_PATH=/api` MCP endpoint доступен по `/api/mcp`.

Доступные инструменты (используются строго последовательно):

- `search_books` — поиск книг по `q`, `author`, `title`.
- `export_book_to_s3` — экспорт одной выбранной книги в S3/MinIO по `book_id`.
- `send_book_to_email` — отправка уже выгруженной в S3 книги на e-mail через n8n-вебхук (`bucket` и `file_key` из ответа `export_book_to_s3`).

## Тестирование

 Тестирование запускается внутри контейнера:

```bash
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose.yml run --rm app sh -c "pytest"
docker-compose -f docker-compose.yml down
```

`docker-compose.yml` поднимает зависимости приложения, включая Elasticsearch (используется для поиска книг).

## Ручное тестирование

```bash
docker-compose -f docker-compose.yml up -d

```
Далее нужно выполнить запросы через curl к эндпоинтам.

## Linting

Запуск линтера (Ruff) внутри контейнера:

```bash
docker-compose -f docker-compose.yml run --rm app sh -c "ruff check ."
```
