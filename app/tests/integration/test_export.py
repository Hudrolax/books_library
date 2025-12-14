from __future__ import annotations

import asyncio
import zipfile

import boto3
from botocore.client import Config
from httpx import AsyncClient
import pytest

from config.config import settings


def _make_s3_client(s3_test_config):
    return boto3.client(
        "s3",
        endpoint_url=s3_test_config["endpoint"],
        aws_access_key_id=s3_test_config["access_key"],
        aws_secret_access_key=s3_test_config["secret_key"],
        region_name=s3_test_config["region"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


async def _empty_bucket(s3_test_config) -> None:
    def _empty():
        s3 = _make_s3_client(s3_test_config)
        resp = s3.list_objects_v2(Bucket=s3_test_config["bucket"])
        contents = resp.get("Contents") or []
        if not contents:
            return
        s3.delete_objects(
            Bucket=s3_test_config["bucket"],
            Delete={"Objects": [{"Key": obj["Key"]} for obj in contents]},
        )

    await asyncio.to_thread(_empty)


@pytest.mark.asyncio
async def test_export_uploads_to_real_s3(
    client: AsyncClient,
    ensure_s3_available,
    s3_test_config,
    tmp_path,
    monkeypatch,
):
    await _empty_bucket(s3_test_config)

    book_id = 29495
    archive_name = "fb2-000516-689800_lost.zip"
    file_name = "687130.fb2"
    file_content = b"hello fb2"

    archive_path = tmp_path / archive_name
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr(file_name, file_content)

    monkeypatch.setattr(settings, "BOOKS_ARCHIVES_PATH", tmp_path)
    monkeypatch.setattr(settings, "S3_ENDPOINT", s3_test_config["endpoint"])
    monkeypatch.setattr(settings, "S3_ACCESS_KEY", s3_test_config["access_key"])
    monkeypatch.setattr(settings, "S3_SECRET_KEY", s3_test_config["secret_key"])
    monkeypatch.setattr(settings, "S3_BUCKET", s3_test_config["bucket"])
    monkeypatch.setattr(settings, "S3_REGION", s3_test_config["region"])

    resp = await client.post(f"/api/v1/books/{book_id}/export")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["bucket"] == s3_test_config["bucket"]
    assert data["existed"] is False
    assert data["key"].startswith(f"{book_id}_")
    assert "_akunin-boris_" in data["key"]
    assert "_skazki-dlya-idiotov_" in data["key"]

    def _read() -> bytes:
        s3 = _make_s3_client(s3_test_config)
        obj = s3.get_object(Bucket=s3_test_config["bucket"], Key=data["key"])
        return obj["Body"].read()

    body = await asyncio.to_thread(_read)
    assert body == file_content


@pytest.mark.asyncio
async def test_export_skips_extraction_when_object_exists_in_s3(
    client: AsyncClient,
    ensure_s3_available,
    s3_test_config,
    tmp_path,
    monkeypatch,
):
    await _empty_bucket(s3_test_config)

    book_id = 29495
    archive_name = "fb2-000516-689800_lost.zip"
    file_name = "687130.fb2"
    file_content = b"hello fb2"

    archive_path = tmp_path / archive_name
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr(file_name, file_content)

    monkeypatch.setattr(settings, "BOOKS_ARCHIVES_PATH", tmp_path)
    monkeypatch.setattr(settings, "S3_ENDPOINT", s3_test_config["endpoint"])
    monkeypatch.setattr(settings, "S3_ACCESS_KEY", s3_test_config["access_key"])
    monkeypatch.setattr(settings, "S3_SECRET_KEY", s3_test_config["secret_key"])
    monkeypatch.setattr(settings, "S3_BUCKET", s3_test_config["bucket"])
    monkeypatch.setattr(settings, "S3_REGION", s3_test_config["region"])

    resp1 = await client.post(f"/api/v1/books/{book_id}/export")
    assert resp1.status_code == 200, resp1.text
    key = resp1.json()["key"]

    # Удаляем архив, чтобы доказать: второй вызов не распаковывает заново
    archive_path.unlink()

    resp2 = await client.post(f"/api/v1/books/{book_id}/export")
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["key"] == key
    assert resp2.json()["existed"] is True
