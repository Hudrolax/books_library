from pydantic import BaseModel, Field


class BooksSearchNoResultsResponse(BaseModel):
    detail: str = Field(..., description="Пояснение, почему результаты поиска отсутствуют")


class BooksSearchTooManyResultsResponse(BaseModel):
    detail: str = Field(..., description="Пояснение, что результатов слишком много и запрос нужно уточнить")
