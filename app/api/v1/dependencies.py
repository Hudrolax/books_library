from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from composition import build_book_service, build_file_storage
from domain.interfaces.storage import IFileStorage
from domain.services.book_service import BookService
from infrastructure.db.db import get_db


def get_file_storage() -> IFileStorage:
    return build_file_storage()


async def get_book_service(
    db: AsyncSession = Depends(get_db),
    storage: IFileStorage = Depends(get_file_storage),
) -> BookService:
    return build_book_service(db, storage)
