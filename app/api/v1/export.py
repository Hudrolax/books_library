from fastapi import APIRouter, Depends, HTTPException

from domain.exceptions import NotFoundError, StorageUnavailableError, ValueException
from domain.services.book_service import BookService

from .dependencies import get_book_service
from .schemas.export import ExportBookResponse


router = APIRouter(prefix="/books", tags=["export"])


@router.post("/{book_id}/export", response_model=ExportBookResponse)
async def export_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> ExportBookResponse:
    try:
        data = await service.export_book_to_s3(book_id)
        return ExportBookResponse.model_validate(data)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    except ValueException as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except StorageUnavailableError as ex:
        raise HTTPException(status_code=503, detail=str(ex))
