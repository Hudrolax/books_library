import re


_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)

_CYRILLIC_E = "е"
_CYRILLIC_YO = "ё"


def build_fts5_match_query(user_query: str) -> str:
    """
    Преобразует пользовательский ввод (обычный текст) в безопасный MATCH-запрос для SQLite FTS5.

    Почему нужно:
    - FTS5 парсит MATCH как выражение со спец-операторами. Ввод вроде "Акунин - Весь мир театр"
      может интерпретироваться как FTS-операторы и приводить к OperationalError (например: "no such column: ...").

    Стратегия:
    - извлекаем "слова" (unicode letters/digits),
    - каждое слово экранируем как точный терм в двойных кавычках,
    - термы объединяем через AND,
    - дополнительно учитываем частую пользовательскую замену `ё -> е` (и наоборот), чтобы запрос
      `Черный` находил `Чёрный` без изменения индекса.
    """

    return _build_fts5_query_part(user_query, column=None)


def build_books_fts5_match_query(*, author: str | None = None, title: str | None = None, q: str | None = None) -> str:
    """
    Собирает безопасный MATCH-запрос для books_fts с поддержкой:
    - поиска по автору (колонка `author`),
    - поиска по названию (колонка `title`),
    - комбинированного поиска (AND между частями).

    Примечание:
    - `q` — общий поиск по всем колонкам (backward-compatible поведение старого /search?q=...).
    - Для колонок квалификация применяется к каждому терму, чтобы выражения с OR были корректны и безопасны.
    """

    parts: list[str] = []

    if author:
        part = _build_fts5_query_part(author, column="author")
        if part:
            parts.append(part)

    if title:
        part = _build_fts5_query_part(title, column="title")
        if part:
            parts.append(part)

    if q:
        part = _build_fts5_query_part(q, column=None)
        if part:
            parts.append(part)

    return " AND ".join(parts)


def _build_fts5_query_part(user_query: str | None, *, column: str | None) -> str:
    tokens = _TOKEN_RE.findall(user_query or "")
    if not tokens:
        return ""

    if column is not None and column not in {"author", "title"}:
        raise ValueError(f"Unsupported FTS column: {column}")

    # В кавычках FTS5 принимает "" как экранирование кавычки внутри терма.
    def _escape(term: str) -> str:
        return term.replace('"', '""')

    def _qualify(term: str) -> str:
        if column is None:
            return term
        return f"{column}:{term}"

    def _variants(token: str) -> set[str]:
        folded = token.casefold()
        variants: set[str] = {folded}

        if _CYRILLIC_YO in folded:
            variants.add(folded.replace(_CYRILLIC_YO, _CYRILLIC_E))
        if _CYRILLIC_E in folded:
            variants.add(folded.replace(_CYRILLIC_E, _CYRILLIC_YO))

        return variants

    def _build_token_expr(token: str) -> str:
        variants = _variants(token)
        qualified_terms = [_qualify(f"\"{_escape(v)}\"") for v in sorted(variants)]
        if len(qualified_terms) == 1:
            return qualified_terms[0]
        return f"({' OR '.join(qualified_terms)})"

    return " AND ".join(_build_token_expr(token) for token in tokens)
