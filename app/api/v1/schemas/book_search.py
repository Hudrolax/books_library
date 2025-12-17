from pydantic import BaseModel, Field


class BooksSearchNoResultsResponse(BaseModel):
    detail: str = Field(..., description="Пояснение, почему результаты поиска отсутствуют")
