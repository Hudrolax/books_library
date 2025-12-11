import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "library.db")


def setup_fts():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create FTS5 virtual table using 'books' as external content
        print("Creating FTS5 virtual table 'books_fts'...")
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
                title, 
                author, 
                content='books', 
                content_rowid='id'
            );
        """)

        # Initial population / rebuild index
        print("Rebuilding FTS index...")
        cursor.execute("INSERT INTO books_fts(books_fts) VALUES('rebuild');")

        # Create triggers to keep FTS in sync (optional given static DB requirement,
        # but good practice if updates ever happen)
        print("Creating triggers...")
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON books BEGIN
              INSERT INTO books_fts(rowid, title, author) VALUES (new.id, new.title, new.author);
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON books BEGIN
              INSERT INTO books_fts(books_fts, rowid, title, author) VALUES('delete', old.id, old.title, old.author);
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON books BEGIN
              INSERT INTO books_fts(books_fts, rowid, title, author) VALUES('delete', old.id, old.title, old.author);
              INSERT INTO books_fts(rowid, title, author) VALUES (new.id, new.title, new.author);
            END;
        """)

        conn.commit()
        print("FTS setup completed successfully.")

    except Exception as e:
        print(f"Error setting up FTS: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    setup_fts()
