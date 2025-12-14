from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from domain.interfaces.storage import IFileStorage
from domain.models.book import Book
from domain.services.book_service import BookService
from infrastructure.db.db import get_db
from infrastructure.db.models.book_orm import BookORM
from infrastructure.repositories.book_repo import BookRepo


def get_file_storage() -> IFileStorage:
    from infrastructure.storage.s3_storage import S3Storage

    return S3Storage(
        endpoint_url=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket=settings.S3_BUCKET,
        region=settings.S3_REGION,
    )


async def get_book_service(
    db: AsyncSession = Depends(get_db),
    storage: IFileStorage = Depends(get_file_storage),
) -> BookService:
    repo: BookRepo = BookRepo(db, Book, BookORM)
    return BookService(
        repo,
        storage,
        archives_path=settings.BOOKS_ARCHIVES_PATH,
        s3_bucket=settings.S3_BUCKET,
    )
