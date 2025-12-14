import re


_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)


def build_fts5_match_query(user_query: str) -> str:
    """
    Преобразует пользовательский ввод (обычный текст) в безопасный MATCH-запрос для SQLite FTS5.

    Почему нужно:
    - FTS5 парсит MATCH как выражение со спец-операторами. Ввод вроде "Акунин - Весь мир театр"
      может интерпретироваться как FTS-операторы и приводить к OperationalError (например: "no such column: ...").

    Стратегия:
    - извлекаем "слова" (unicode letters/digits),
    - каждое слово экранируем как точный терм в двойных кавычках,
    - термы объединяем пробелами (в FTS5 это AND).
    """

    tokens = _TOKEN_RE.findall(user_query or "")
    if not tokens:
        return ""

    # В кавычках FTS5 принимает "" как экранирование кавычки внутри терма.
    return " ".join(f"\"{token.replace('\"', '\"\"')}\"" for token in tokens)

