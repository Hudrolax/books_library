# Колонки таблицы `books` в `librarry.db`

| cid | name               | type    | notnull | dflt_value | pk |
| --- | ------------------ | ------- | ------- | ---------- | -- |
| 0   | id                 | INTEGER | 0       | NULL       | 1  |
| 1   | author             | TEXT    | 0       | NULL       | 0  |
| 2   | title              | TEXT    | 0       | NULL       | 0  |
| 3   | archive_name       | TEXT    | 0       | NULL       | 0  |
| 4   | file_name          | TEXT    | 0       | NULL       | 0  |
| 5   | file_size_mb       | REAL    | 0       | NULL       | 0  |
| 6   | genre              | TEXT    | 0       | NULL       | 0  |
| 7   | author_first_name  | TEXT    | 0       | NULL       | 0  |
| 8   | author_last_name   | TEXT    | 0       | NULL       | 0  |
| 9   | book_title         | TEXT    | 0       | NULL       | 0  |
| 10  | annotation         | TEXT    | 0       | NULL       | 0  |
| 11  | lang               | TEXT    | 0       | NULL       | 0  |
| 12  | publish_book_name  | TEXT    | 0       | NULL       | 0  |
| 13  | publisher          | TEXT    | 0       | NULL       | 0  |
| 14  | city               | TEXT    | 0       | NULL       | 0  |
| 15  | year               | TEXT    | 0       | NULL       | 0  |
| 16  | isbn               | TEXT    | 0       | NULL       | 0  |

Источник: `PRAGMA table_info(books);` выполненный 2025-12-09.
