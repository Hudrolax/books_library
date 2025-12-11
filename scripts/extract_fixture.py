import json
import os
import sqlite3


DB_PATH = "library.db"
OUTPUT_PATH = "app/tests/fixtures/akunin_books.json"


def extract():
    if not os.path.exists(DB_PATH):
        print("library.db not found")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Selecting books by Akunin. Adjust query if needed to match "Акунин" in author.
    cursor.execute("SELECT * FROM books WHERE author LIKE '%Акунин%' LIMIT 50")
    rows = cursor.fetchall()

    books = [dict(row) for row in rows]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(books)} books to {OUTPUT_PATH}")
    conn.close()


if __name__ == "__main__":
    extract()
