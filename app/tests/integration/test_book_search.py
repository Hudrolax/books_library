from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_books_integration(client: AsyncClient):
    # Используем `client` фикстуру (предполагаем наличие conftest.py)
    # В conftest.py мы загрузили данные из акунин_books.json
    # Попробуем найти конкретную книгу, которая точно есть в фикстуре.
    # Например, если мы знаем, что там есть "Азазель" или просто ищем "Акунин"

    query = "Акунин"
    response = await client.get(f"/api/v1/books/search?q={query}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Should return results from loaded fixture"

    # Проверяем, что вернулись реальные данные
    first_book = data[0]
    assert "author" in first_book
    assert "title" in first_book

    # Простейшая проверка: query должна встречаться в book (FTS match)
    # Но так как мы ищем по автору "Акунин", у всех книг должен быть этот автор (или в title)
    # Поскольку фикстура состоит ТОЛЬКО из книг Акунина (extract query was WHERE author LIKE 'Акунин'),
    # то поиск 'Акунин' должен вернуть их.

    # Можно проверить более детально, если загрузим фикстуру в тесте
    import json
    import os

    fixture_path = "/app/tests/fixtures/akunin_books.json"
    if not os.path.exists(fixture_path):
        fixture_path = os.path.join(os.path.dirname(__file__), "../fixtures/akunin_books.json")

    with open(fixture_path, "r") as f:
        expected_books = json.load(f)

    # Проверим, что найденная книга есть в наших ожидаемых
    found_ids = {b["id"] for b in data}
    expected_ids = {b["id"] for b in expected_books}

    # Мы могли найти не все (limit, rank), но найденные должны быть из expected
    assert found_ids.issubset(expected_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_books_empty_query(client: AsyncClient):
    response = await client.get("/api/v1/books/search")
    # FastAPI возвращает 422 для missing query param
    assert response.status_code == 422
