from __future__ import annotations

import logging
from pathlib import Path

from domain.exceptions import StorageUnavailableError
from domain.interfaces.storage import IFileStorage


logger = logging.getLogger(__name__)


class S3Storage(IFileStorage):
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region
        try:
            import aioboto3  # type: ignore
        except ModuleNotFoundError as ex:
            raise ModuleNotFoundError(
                "Пакет 'aioboto3' не установлен. Установите зависимости проекта (см. pyproject.toml)."
            ) from ex
        self._session = aioboto3.Session()

    async def file_exists(self, *, key: str) -> bool:
        from botocore.client import Config
        from botocore.exceptions import ClientError, EndpointConnectionError

        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 5, "mode": "standard"},
            ),
        ) as client:
            try:
                await client.head_object(Bucket=self._bucket, Key=key)
                return True
            except ClientError as err:
                code = (err.response or {}).get("Error", {}).get("Code")
                if code in {"404", "NoSuchKey", "NotFound"}:
                    return False
                raise
            except EndpointConnectionError as err:
                logger.exception(
                    "S3 endpoint недоступен при head_object (endpoint=%s bucket=%s key=%s)",
                    self._endpoint_url,
                    self._bucket,
                    key,
                )
                raise StorageUnavailableError("S3/MinIO недоступен") from err

    async def upload_file(self, *, key: str, path: Path, content_type: str | None = None) -> None:
        from botocore.client import Config
        from botocore.exceptions import EndpointConnectionError

        extra_args = {"ContentType": content_type} if content_type else None
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 5, "mode": "standard"},
            ),
        ) as client:
            try:
                await client.upload_file(
                    Filename=str(path),
                    Bucket=self._bucket,
                    Key=key,
                    ExtraArgs=extra_args,
                )
            except EndpointConnectionError as err:
                logger.exception(
                    "S3 endpoint недоступен при upload_file (endpoint=%s bucket=%s key=%s path=%s)",
                    self._endpoint_url,
                    self._bucket,
                    key,
                    path,
                )
                raise StorageUnavailableError("S3/MinIO недоступен") from err
