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

    tokens = _TOKEN_RE.findall(user_query or "")
    if not tokens:
        return ""

    # В кавычках FTS5 принимает "" как экранирование кавычки внутри терма.
    def _escape(term: str) -> str:
        return term.replace('"', '""')

    def _build_token_expr(token: str) -> str:
        folded = token.casefold()
        variants: set[str] = {folded}

        if _CYRILLIC_YO in folded:
            variants.add(folded.replace(_CYRILLIC_YO, _CYRILLIC_E))
        if _CYRILLIC_E in folded:
            variants.add(folded.replace(_CYRILLIC_E, _CYRILLIC_YO))

        if len(variants) == 1:
            v = next(iter(variants))
            return f"\"{_escape(v)}\""

        parts = " OR ".join(f"\"{_escape(v)}\"" for v in sorted(variants))
        return f"({parts})"

    return " AND ".join(_build_token_expr(token) for token in tokens)
