from sqlalchemy import Column, Float, Integer, Text

from .base_model_orm import BaseORMModel


class BookORM(BaseORMModel):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    author = Column(Text, index=True)
    title = Column(Text, index=True)
    archive_name = Column(Text)
    file_name = Column(Text)
    file_size_mb = Column(Float)
    genre = Column(Text)
    author_first_name = Column(Text)
    author_last_name = Column(Text)
    book_title = Column(Text)
    annotation = Column(Text)
    lang = Column(Text)
    publish_book_name = Column(Text)
    publisher = Column(Text)
    city = Column(Text)
    year = Column(Text)
    isbn = Column(Text)
