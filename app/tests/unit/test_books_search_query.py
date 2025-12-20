from infrastructure.search.books_index import build_books_search_query


def test_build_books_search_query_empty_is_match_none():
    assert build_books_search_query(q=None, author=None, title=None) == {"match_none": {}}


def test_build_books_search_query_q_uses_title_and_author_fields():
    q = build_books_search_query(q="Акунин Азазель", author=None, title=None)
    must = q["bool"]["must"]
    assert len(must) == 1
    mm = must[0]["multi_match"]
    assert mm["type"] == "bool_prefix"
    assert mm["operator"] == "and"
    assert "title" in mm["fields"]
    assert "author" in mm["fields"]


def test_build_books_search_query_supports_author_and_title_filters():
    q = build_books_search_query(q=None, author="Акунин", title="Азазель")
    must = q["bool"]["must"]
    assert len(must) == 2
    assert must[0]["multi_match"]["fields"][0].startswith("author")
    assert must[1]["multi_match"]["fields"][0].startswith("title")

