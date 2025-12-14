# Book Library

## Testing

 To run tests, use the following command:

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml run --rm app sh -c "pytest"
docker-compose -f docker-compose.dev.yml down
```

## Linting

Запуск линтера (Ruff) внутри контейнера:

```bash
docker-compose -f docker-compose.dev.yml run --rm app sh -c "ruff check ."
```
