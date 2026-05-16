from pathlib import Path

import pytest

from domain.exceptions import ValueException
from domain.services.book_service import BookService


class _Storage:
    def __init__(self, *, exists: bool) -> None:
        self._exists = exists
        self.checked_key: str | None = None

    async def file_exists(self, *, key: str) -> bool:
        self.checked_key = key
        return self._exists

    async def upload_file(self, *, key, path, content_type=None) -> None:  # pragma: no cover
        raise AssertionError("upload_file не должен вызываться в этом тесте")


class _EmailSender:
    def __init__(self) -> None:
        self.kwargs: dict[str, str] | None = None

    async def send_book(self, *, bucket: str, file_key: str, to: str, subject: str, text: str):
        self.kwargs = {
            "bucket": bucket,
            "file_key": file_key,
            "to": to,
            "subject": subject,
            "text": text,
        }
        return {
            "ok": True,
            "status_code": 200,
            "provider_response": {"message": "The file has been successfully sent to email."},
            "detail": "The file has been successfully sent to email.",
        }


def _service(storage: _Storage, email_sender: _EmailSender) -> BookService:
    return BookService(
        repository=object(),  # type: ignore[arg-type]
        storage=storage,  # type: ignore[arg-type]
        email_sender=email_sender,  # type: ignore[arg-type]
        archives_path=Path("/tmp"),
        s3_bucket="books",
    )


@pytest.mark.asyncio
async def test_send_book_to_email_delegates_when_file_in_s3() -> None:
    storage = _Storage(exists=True)
    email_sender = _EmailSender()
    service = _service(storage, email_sender)

    result = await service.send_book_to_email(
        bucket="books",
        file_key="103582_akunin-boris_azazel_0_39.fb2",
        to="hudro795@gmail.com",
        subject="Ваша книга",
        text="Получи свою книгу!",
    )

    assert result == {
        "ok": True,
        "status_code": 200,
        "provider_response": {"message": "The file has been successfully sent to email."},
        "detail": "The file has been successfully sent to email.",
    }
    assert storage.checked_key == "103582_akunin-boris_azazel_0_39.fb2"
    assert email_sender.kwargs is not None


@pytest.mark.asyncio
async def test_send_book_to_email_raises_when_file_not_in_s3() -> None:
    storage = _Storage(exists=False)
    email_sender = _EmailSender()
    service = _service(storage, email_sender)

    with pytest.raises(ValueException):
        await service.send_book_to_email(
            bucket="books",
            file_key="missing.fb2",
            to="hudro795@gmail.com",
            subject="Ваша книга",
            text="Получи свою книгу!",
        )

    assert email_sender.kwargs is None
