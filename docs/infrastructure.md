# Инфраструктура

- Менеджер зависимостей: `uv` (виртуальная среда в `.venv`, кэш в `.uvcache`).
- Docker: multi-stage образ на `python:3.13.4-alpine3.22`; build-stage ставит только базовые dev-пакеты (`build-base`, `linux-headers`, `python3-dev`, `libffi-dev`, `pkgconf`) без Rust, т.к. сборка `tiktoken` больше не требуется.
- База данных по умолчанию: файл SQLite `librarry.db` в корне репозитория, URL формируется как `sqlite+aiosqlite:///<абсолютный_путь>`. Переменная окружения `DATABASE_URL` может переопределить подключение; пустое значение в `.env` будет проигнорировано и заменено на SQLite по умолчанию.
