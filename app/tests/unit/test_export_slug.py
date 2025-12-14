from domain.services.book_service import BookService


def test_slug_transliterates_cyrillic_to_readable_ascii() -> None:
    assert BookService._slug("Акунин Борис") == "akunin-boris"
    assert BookService._slug("Сказки для идиотов") == "skazki-dlya-idiotov"

