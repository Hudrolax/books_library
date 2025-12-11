from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_books_integration(client: AsyncClient):
    # Используем `client` фикстуру (предполагаем наличие conftest.py)
    # В conftest.py мы загрузили данные из акунин_books.json
    # Попробуем найти конкретную книгу, которая точно есть в фикстуре.
    # Например, если мы знаем, что там есть "Азазель" или просто ищем "Акунин"

    # 1. Test success with specific query (few results)
    query_success = "Азазель"
    response = await client.get(f"/api/v1/books/search?q={query_success}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert 0 < len(data) <= 20

    # Check that results match the query
    for book in data:
        # Simplified check, assuming full text search matches one of these fields
        assert query_success.lower() in book["title"].lower() or query_success.lower() in book["author"].lower()

    # 2. Test failure with broad query (too many results)
    # "Акунин" key matches almost all books in the fixture > 20
    query_fail = "Акунин"
    response_fail = await client.get(f"/api/v1/books/search?q={query_fail}")
    assert response_fail.status_code == 400
    assert response_fail.json()["detail"] == "Found too many matching books. Please refine your search."


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_books_empty_query(client: AsyncClient):
    response = await client.get("/api/v1/books/search")
    # FastAPI возвращает 422 для missing query param
    assert response.status_code == 422
