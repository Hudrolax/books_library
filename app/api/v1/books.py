from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from domain.models.book import Book
from domain.services.book_service import BookService

from .dependencies import get_book_service


router = APIRouter(prefix="/books", tags=["books"])


@router.get("/search", response_model=List[Book])
async def search_books(
    q: str = Query(..., description="Поисковый запрос"),
    service: BookService = Depends(get_book_service),
) -> List[Book]:
    try:
        return await service.search(q)
    except Exception as e:  # noqa: BLE001
        from domain.exceptions import BooksNotFoundError, TooManyResultsError

        if isinstance(e, TooManyResultsError):
            raise HTTPException(status_code=400, detail=str(e))
        if isinstance(e, BooksNotFoundError):
            raise HTTPException(status_code=404, detail=str(e))
        raise
