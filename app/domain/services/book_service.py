import hashlib
import logging
import mimetypes
from pathlib import Path
import re
import tempfile
from typing import List
import unicodedata
import zipfile

from domain.exceptions import ValueException
from domain.interfaces.storage import IFileStorage

from ..interfaces.book_ifaces import IBookRepoProtocol, IBookService
from ..models.book import Book, BookDict


logger = logging.getLogger(__name__)


class BookService(IBookService):
    repository: IBookRepoProtocol

    def __init__(
        self,
        repository: IBookRepoProtocol,
        storage: IFileStorage,
        *,
        archives_path: Path,
        s3_bucket: str,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.archives_path = archives_path
        self.s3_bucket = s3_bucket

    async def read(self, filters: BookDict) -> Book:
        return await self.repository.read(filters=filters)

    async def list(self, filters: BookDict) -> List[Book]:
        return await self.repository.list(filters=filters)

    async def search(
        self,
        *,
        q: str | None = None,
        author: str | None = None,
        title: str | None = None,
    ) -> List[Book]:
        limit = 50
        # Запрашиваем на 1 больше, чтобы понять, есть ли еще результаты
        books = await self.repository.search(q=q, author=author, title=title, limit=limit + 1)

        if not books:
            from domain.exceptions import BooksNotFoundError

            raise BooksNotFoundError(
                "По твоему запросу не найдено ни одной книги. "
                "Попробуй измени строку поиска. Например оставь только имя автора или только название книги, "
                "или часть названия, или часть фамилии автора. Можно попробовать удалить из строки поиска лишние символы типа тире, "
                "если они есть."
            )

        if len(books) > limit:
            from domain.exceptions import TooManyResultsError

            raise TooManyResultsError(
                "Запрос поиска находит больше 50ти книг по запрошенным данным. Попробуй уточнить запрос."
            )

        return books

    async def export_book_to_s3(self, book_id: int) -> dict[str, str | bool]:
        book = await self.repository.read(filters={"id": book_id})

        if not book.archive_name:
            raise ValueException("У книги отсутствует archive_name")
        if not book.file_name:
            raise ValueException("У книги отсутствует file_name")

        object_key = self._build_object_key(book)

        existed = await self.storage.file_exists(key=object_key)
        if not existed:
            archive_path = self.archives_path / Path(book.archive_name).name
            member_name = book.file_name

            if not archive_path.exists():
                raise ValueException(f"Архив не найден: {archive_path}")
            if not zipfile.is_zipfile(archive_path):
                raise ValueException(f"Неподдерживаемый формат архива: {archive_path}")

            with tempfile.TemporaryDirectory(prefix="book_export_") as tmp_dir:
                extracted_path = await self._extract_from_zip(
                    archive_path=archive_path,
                    member_name=member_name,
                    dest_dir=Path(tmp_dir),
                )
                content_type, _ = mimetypes.guess_type(extracted_path.name)
                await self.storage.upload_file(key=object_key, path=extracted_path, content_type=content_type)

        return {"bucket": self.s3_bucket, "key": object_key, "existed": existed}

    @staticmethod
    def _transliterate_cyrillic(value: str) -> str:
        mapping = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "yo",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "kh",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "shch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
            # Часто встречающиеся дополнительные кириллические буквы (укр/бел)
            "і": "i",
            "ї": "yi",
            "є": "ye",
            "ґ": "g",
            "ў": "u",
        }

        folded = value.casefold()
        parts: list[str] = []
        for ch in folded:
            parts.append(mapping.get(ch, ch))
        return "".join(parts)

    @staticmethod
    def _slug(value: str) -> str:
        raw = value.strip()
        if not raw:
            return "unknown"

        transliterated = BookService._transliterate_cyrillic(raw)
        normalized = unicodedata.normalize("NFKD", transliterated)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
        ascii_value = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
        if ascii_value:
            return ascii_value[:80]

        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
        return f"u-{digest}"

    def _build_object_key(self, book: Book) -> str:
        author = book.author or "unknown"
        title = book.title or book.book_title or "unknown"
        size = book.file_size_mb
        size_str = "unknown"
        if isinstance(size, (int, float)):
            normalized = f"{size:.2f}".rstrip("0").rstrip(".")
            size_str = normalized.replace(".", "_")

        ext = Path(book.file_name or "").suffix
        ext = ext if ext else ""

        return f"{book.id}_{self._slug(author)}_{self._slug(title)}_{size_str}{ext}"

    @staticmethod
    async def _extract_from_zip(*, archive_path: Path, member_name: str, dest_dir: Path) -> Path:
        def _extract() -> Path:
            with zipfile.ZipFile(archive_path) as zf:
                extracted = zf.extract(member_name, path=dest_dir)
                return Path(extracted)

        try:
            import asyncio

            return await asyncio.to_thread(_extract)
        except KeyError as ex:
            raise ValueException(f"Файл не найден в архиве: {member_name}") from ex
