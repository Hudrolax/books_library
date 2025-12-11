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
    return await service.search(q)
