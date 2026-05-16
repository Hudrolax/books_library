import httpx
import pytest

from domain.exceptions import EmailSendError
from infrastructure.email.n8n_email_sender import N8nEmailSender


def _patch_transport(monkeypatch, handler) -> None:
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def _sender() -> N8nEmailSender:
    return N8nEmailSender(webhook_url="https://n8n.example/webhook/abc", timeout_s=5.0)


@pytest.mark.asyncio
async def test_success_200_passes_through_json(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": "The file has been successfully sent to email."})

    _patch_transport(monkeypatch, handler)

    result = await _sender().send_book(
        bucket="books", file_key="k.fb2", to="a@b.c", subject="s", text="t"
    )

    assert result == {
        "ok": True,
        "status_code": 200,
        "provider_response": {"message": "The file has been successfully sent to email."},
        "detail": "The file has been successfully sent to email.",
    }


@pytest.mark.asyncio
async def test_n8n_500_is_not_raised_and_body_passed_through(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "SMTP timeout", "code": "EMAIL_FAILED"})

    _patch_transport(monkeypatch, handler)

    result = await _sender().send_book(
        bucket="books", file_key="k.fb2", to="a@b.c", subject="s", text="t"
    )

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert result["provider_response"] == {"error": "SMTP timeout", "code": "EMAIL_FAILED"}
    assert result["detail"] == "n8n вернул ошибку: HTTP 500"


@pytest.mark.asyncio
async def test_non_json_body_yields_null_provider_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain text")

    _patch_transport(monkeypatch, handler)

    result = await _sender().send_book(
        bucket="books", file_key="k.fb2", to="a@b.c", subject="s", text="t"
    )

    assert result["ok"] is True
    assert result["provider_response"] is None
    assert result["detail"] == "Книга отправлена на e-mail"


@pytest.mark.asyncio
async def test_transport_error_raises_email_send_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    _patch_transport(monkeypatch, handler)

    with pytest.raises(EmailSendError):
        await _sender().send_book(
            bucket="books", file_key="k.fb2", to="a@b.c", subject="s", text="t"
        )
