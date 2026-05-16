from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from domain.interfaces.email_sender import IEmailSender
from domain.interfaces.storage import IFileStorage
from domain.models.book import Book
from domain.services.book_service import BookService
from infrastructure.db.models.book_orm import BookORM
from infrastructure.email.n8n_email_sender import N8nEmailSender
from infrastructure.repositories.book_repo import BookRepo
from infrastructure.storage.s3_storage import S3Storage


def build_file_storage() -> IFileStorage:
    return S3Storage(
        endpoint_url=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket=settings.S3_BUCKET,
        region=settings.S3_REGION,
    )


def build_email_sender() -> IEmailSender:
    return N8nEmailSender(
        webhook_url=settings.N8N_EMAIL_WEBHOOK_URL,
        timeout_s=settings.N8N_EMAIL_WEBHOOK_TIMEOUT_S,
    )


def build_book_service(
    db: AsyncSession,
    storage: IFileStorage | None = None,
    email_sender: IEmailSender | None = None,
) -> BookService:
    repo: BookRepo = BookRepo(db, Book, BookORM)
    return BookService(
        repo,
        storage or build_file_storage(),
        email_sender or build_email_sender(),
        archives_path=settings.BOOKS_ARCHIVES_PATH,
        s3_bucket=settings.S3_BUCKET,
    )
