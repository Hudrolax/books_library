# Architecture of the "Book Library" Project

## Overview

This project is a backend service for a Book Library application, built with modern Python technologies. It aims to provide a robust API for managing and retrieving book information.

## Technology Stack

- **Language**: Python 3.13
- **Web Framework**: FastAPI (v0.115+)
- **MCP**: FastMCP (HTTP MCP server exposed by the FastAPI app)
- **Server**: Uvicorn
- **Database ORM**: SQLAlchemy (AsyncIO extension)
- **Object Storage**: S3-compatible (MinIO) + `aioboto3` (async S3 client)
- **Containerization**: Docker & Docker Compose
- **Dependency Management**: Standard `pip` / `pyproject.toml`

## Project Structure

The application follows a clean architecture pattern, separating concerns into distinct layers:

### 1. `app/api` (Interface Layer)

Contains the FastAPI routers and endpoints.

- **`v1/`**: Version 1 of the API.
  - `healthcheck_router.py`: Provides health monitoring endpoints (e.g., `/api/v1/healthcheck`).
  - `export.py`: Экспорт книги в S3/MinIO (например, `POST /api/v1/books/{book_id}/export`); в ответе возвращаются `bucket`, `key`, `existed` (ссылка не формируется, загрузку клиент делает сам по `bucket+key`). При недоступности S3/MinIO эндпоинт отвечает `503`.

### 1.1. `app/mcp_server` (MCP Interface Layer)

Содержит FastMCP сервер, подключённый к основному FastAPI-приложению на `/mcp` (с учётом `API_ROOT_PATH` внешний путь по умолчанию — `/api/mcp`).

MCP-инструменты образуют строгий сценарий из трёх шагов (он же описан в `instructions` сервера): поиск → выбор ровно одной книги → экспорт в S3 → отправка на e-mail.

- `search_books`: шаг 1 — поиск книг. Принимает поисковые параметры `q`, `author`, `title` и использует тот же `BookService.search`.
- `export_book_to_s3`: шаг 2 — экспорт одной выбранной книги в S3/MinIO. Принимает `book_id`, использует `BookService.export_book_to_s3` и возвращает `bucket`, `key`, `existed`.
- `send_book_to_email`: шаг 3 — отправка уже выгруженной в S3 книги на e-mail. Принимает `bucket`, `file_key` (из ответа `export_book_to_s3`), `to`, `subject`, `text`; использует `BookService.send_book_to_email`. Сервис сначала проверяет наличие файла в S3 (`IFileStorage.file_exists`) и только потом дёргает n8n-вебхук, поэтому отправка возможна только после успешного экспорта. n8n штатно отвечает JSON и при успехе (2xx), и при неудаче доставки (например 500); этот JSON как есть пробрасывается клиенту в поле `provider_response`. Статус `ok` ставится только при 2xx, иначе `email_send_failed` (с телом-объяснением в `provider_response`); транспортная недоступность n8n даёт `email_send_failed` и `provider_response = null`.
- MCP-инструменты возвращают структурированные статусы (`ok`, `validation_error`, `no_results`, `too_many_results`, `not_found`, `invalid_book_data`, `storage_unavailable`, `not_in_s3`, `email_send_failed`) вместо HTTP-кодов, потому что MCP не является HTTP API для конечного клиента.

### 2. `app/domain` (Domain Layer)

Encapsulates the core business logic and data models. This layer is independent of external frameworks and databases.

- **`models/`**: Pydantic models acting as Domain Entities.
  - `book.py`: Defines the `Book` entity with fields like `id`, `author`, `title`, `isbn`, etc.
- **`services/`**: Business logic implementations (implied).
- **`interfaces/`**: Абстракции для внешних зависимостей (репозитории, S3-хранилище и т.д.).

### 3. `app/infrastructure` (Infrastructure Layer)

Handles external concerns such as database access, file systems, and third-party services.

- **`db/`**: Database configuration and session management.
  - Uses `async_sessionmaker` and `create_async_engine` for asynchronous database operations.
- **`repositories/`**: Concrete implementations of domain interfaces for data persistence.
- **`search/`**: Поиск книг в Elasticsearch.
  - Клиент `AsyncElasticsearch` инициализируется в lifespan приложения и закрывается при shutdown.
  - Индекс книг задаётся через `ELASTICSEARCH_INDEX` (по умолчанию `books`).
  - При первом поисковом запросе (если включено `ELASTICSEARCH_AUTO_INDEX=true`) приложение:
    1) создаёт индекс с маппингом `search_as_you_type` для `title` и `author` и русским анализатором (включая нормализацию `ё→е`),
    2) индексирует книги из БД, если индекс пуст.
  - Эндпоинт `/api/v1/books/search` ищет релевантные `id` в Elasticsearch и затем подтягивает полные записи из БД, сохраняя порядок по релевантности.
- **`storage/`**: Интеграции с внешними хранилищами (например, `S3Storage` для S3/MinIO).
- **`email/`**: Отправка книги на e-mail. `N8nEmailSender` POST-ом обращается к готовому n8n-вебхуку (`N8N_EMAIL_WEBHOOK_URL`) и не содержит собственной email-инфраструктуры. Реализует доменный интерфейс `IEmailSender`; при недоступности/ошибке вебхука бросает `EmailSendError`.

### 4. `app/config`

- `config.py`: Application configuration using Pydantic Settings (reading from `.env` or environment variables).
  - Также хранит настройки пути до архивов книг (`BOOKS_ARCHIVES_PATH`), S3/MinIO (`S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, ...) и n8n-вебхука отправки книги на e-mail (`N8N_EMAIL_WEBHOOK_URL`, `N8N_EMAIL_WEBHOOK_TIMEOUT_S`).
  - `S3_ENDPOINT` нормализуется (обрезаются кавычки/пробелы, убирается хвостовой `/`; если схема не указана — добавляется `http://`).
  - Базовый путь приложения для деплоя за прокси задаётся через `API_ROOT_PATH` (используется как `FastAPI(root_path=...)`, по умолчанию `"/api"`).

### 5. `app/composition.py`

Общий слой сборки зависимостей приложения. Создаёт `S3Storage`, `N8nEmailSender` и `BookService` для разных интерфейсных слоёв. FastAPI dependency-функции и MCP-инструменты используют эти фабрики, чтобы не расходиться в создании репозитория, S3-хранилища, отправщика e-mail и настроек.

## Data Model

### Book

The primary entity is the `Book`, representing a library item. Key attributes include:

- **Core Info**: `title`, `author`, `annotation`, `genre`, `lang`.
- **File Info**: `archive_name`, `file_name`, `file_size_mb`.
- **Publication**: `publisher`, `city`, `year`, `isbn`, `publish_book_name`.

## Development & Deployment

- **Docker**: The application is containerized with a `Dockerfile` and orchestrated via `docker-compose.yml`.
- **Environment**: Configured via environment variables (`DEV`, `DATABASE_URL`, `LOG_LEVEL`, `BOOKS_ARCHIVES_PATH`, S3/MinIO settings, etc.).
