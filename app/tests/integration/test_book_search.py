from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_books_integration(client: AsyncClient, api_url):
    # Используем `client` фикстуру (предполагаем наличие conftest.py)
    # В conftest.py мы загрузили данные из акунин_books.json
    # Попробуем найти конкретную книгу, которая точно есть в фикстуре.
    # Например, если мы знаем, что там есть "Азазель" или просто ищем "Акунин"

    # 1. Test success: search by title only (few results)
    title_success = "Азазель"
    response = await client.get(api_url(f"/v1/books/search?title={title_success}"))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert 0 < len(data) <= 50

    # Check that results match the query
    for book in data:
        # Simplified check, assuming full text search matches one of these fields
        assert title_success.lower() in book["title"].lower()

    # 2. Test success: combined search by author and title (narrower than author-only)
    author_success = "Акунин"
    response_combo = await client.get(api_url(f"/v1/books/search?author={author_success}&title={title_success}"))
    assert response_combo.status_code == 200
    data_combo = response_combo.json()
    assert isinstance(data_combo, list)
    assert 0 < len(data_combo) <= 50
    for book in data_combo:
        assert author_success.lower() in book["author"].lower()
        assert title_success.lower() in book["title"].lower()

    # 3. Test: broad query returns 200 with explanatory message (too many results) via author-only
    # "Акунин" key matches almost all books in the fixture > 50
    response_fail = await client.get(api_url(f"/v1/books/search?author={author_success}"))
    assert response_fail.status_code == 200
    assert response_fail.json()["detail"] == (
        "Запрос поиска находит больше 50ти книг по запрошенным данным. Попробуй уточнить запрос."
    )

    # 4. Test failure with query that returns no results
    query_none = "___no_such_book___"
    response_none = await client.get(api_url(f"/v1/books/search?title={query_none}"))
    assert response_none.status_code == 200
    assert response_none.json()["detail"] == (
        "По твоему запросу не найдено ни одной книги. "
        "Попробуй измени строку поиска. Например оставь только имя автора или только название книги, "
        "или часть названия, или часть фамилии автора. Можно попробовать удалить из строки поиска лишние символы типа тире, "
        "если они есть."
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_books_empty_query(client: AsyncClient, api_url):
    response = await client.get(api_url("/v1/books/search"))
    # Без параметров поиска эндпоинт возвращает 422
    assert response.status_code == 422
