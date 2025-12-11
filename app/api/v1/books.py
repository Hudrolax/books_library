from typing import List

from fastapi import APIRouter, Depends, Query

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
    except Exception as e:
        # Check for TooManyResultsError by name to avoid circular imports or direct dependency if possible,
        # or import it. Here we'll import it inside the function or catch generally if we prefer,
        # but better to import explicitly.
        from domain.exceptions import TooManyResultsError

        if isinstance(e, TooManyResultsError):
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail=str(e))
        raise e
