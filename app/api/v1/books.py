from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from domain.models.book import Book
from domain.services.book_service import BookService

from .dependencies import get_book_service
from .schemas.book_search import BooksSearchNoResultsResponse, BooksSearchTooManyResultsResponse


router = APIRouter(prefix="/books", tags=["books"])


@router.get(
    "/search",
    response_model=List[Book] | BooksSearchNoResultsResponse | BooksSearchTooManyResultsResponse,
)
async def search_books(
    q: str | None = Query(
        None,
        description="Общий поисковый запрос (по автору и названию). Deprecated: предпочитай author/title.",
    ),
    author: str | None = Query(None, description="Поиск по автору"),
    title: str | None = Query(None, description="Поиск по названию"),
    service: BookService = Depends(get_book_service),
) -> List[Book] | BooksSearchNoResultsResponse | BooksSearchTooManyResultsResponse:
    q_norm = q.strip() if q else None
    author_norm = author.strip() if author else None
    title_norm = title.strip() if title else None

    if not q_norm and not author_norm and not title_norm:
        raise HTTPException(
            status_code=422,
            detail="Нужно указать хотя бы один параметр поиска: q, author или title.",
        )

    try:
        return await service.search(q=q_norm, author=author_norm, title=title_norm)
    except Exception as e:  # noqa: BLE001
        from domain.exceptions import BooksNotFoundError, TooManyResultsError

        if isinstance(e, TooManyResultsError):
            return BooksSearchTooManyResultsResponse(detail=str(e))
        if isinstance(e, BooksNotFoundError):
            return BooksSearchNoResultsResponse(detail=str(e))
        raise
