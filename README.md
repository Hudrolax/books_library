# Book Library

## Тестирование

 Тестирование запускается внутри контейнера:

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml run --rm app sh -c "pytest"
docker-compose -f docker-compose.dev.yml down
```

`docker-compose.dev.yml` поднимает зависимости приложения, включая Elasticsearch (используется для поиска книг).

## Ручное тестирование

```bash
docker-compose -f docker-compose.dev.yml up -d

```
Далее нужно выполнить запросы через curl к эндпоинтам.

## Linting

Запуск линтера (Ruff) внутри контейнера:

```bash
docker-compose -f docker-compose.dev.yml run --rm app sh -c "ruff check ."
```
