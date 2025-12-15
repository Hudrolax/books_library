# Architecture of the "Book Library" Project

## Overview

This project is a backend service for a Book Library application, built with modern Python technologies. It aims to provide a robust API for managing and retrieving book information.

## Technology Stack

- **Language**: Python 3.13
- **Web Framework**: FastAPI (v0.115+)
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
  - На старте приложения выполняется проверка наличия SQLite FTS5-таблицы `books_fts`; если таблицы нет — она создаётся и индекс перестраивается (инициализация поиска).
  - Пользовательский поисковый ввод нормализуется в безопасный FTS5 `MATCH`-запрос: термы берутся из «слов» (unicode letters/digits) и экранируются в двойных кавычках; выражение собирается контролируемо (AND/OR/скобки), чтобы не падать на символах вроде `-` и чтобы учитывать частую замену `ё↔е` (например, `Черный` находит `Чёрный`).
- **`repositories/`**: Concrete implementations of domain interfaces for data persistence.
- **`storage/`**: Интеграции с внешними хранилищами (например, `S3Storage` для S3/MinIO).

### 4. `app/config`

- `config.py`: Application configuration using Pydantic Settings (reading from `.env` or environment variables).
  - Также хранит настройки пути до архивов книг (`BOOKS_ARCHIVES_PATH`) и S3/MinIO (`S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, ...).
  - `S3_ENDPOINT` нормализуется (обрезаются кавычки/пробелы, убирается хвостовой `/`; если схема не указана — добавляется `http://`).
  - Базовый путь приложения для деплоя за прокси задаётся через `API_ROOT_PATH` (используется как `FastAPI(root_path=...)`, по умолчанию `"/api"`).

## Data Model

### Book

The primary entity is the `Book`, representing a library item. Key attributes include:

- **Core Info**: `title`, `author`, `annotation`, `genre`, `lang`.
- **File Info**: `archive_name`, `file_name`, `file_size_mb`.
- **Publication**: `publisher`, `city`, `year`, `isbn`, `publish_book_name`.

## Development & Deployment

- **Docker**: The application is containerized with a `Dockerfile` and orchestrated via `docker-compose.yml`.
- **Environment**: Configured via environment variables (`DEV`, `DATABASE_URL`, `LOG_LEVEL`, `BOOKS_ARCHIVES_PATH`, S3/MinIO settings, etc.).
