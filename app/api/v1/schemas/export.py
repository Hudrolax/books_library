from pydantic import BaseModel, Field


class ExportBookResponse(BaseModel):
    bucket: str = Field(..., description="Bucket")
    key: str = Field(..., description="S3 object key")
    existed: bool = Field(..., description="Был ли файл уже в S3")
