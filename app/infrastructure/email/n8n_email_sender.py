from __future__ import annotations

import logging

from domain.exceptions import EmailSendError
from domain.interfaces.email_sender import EmailSendResult, IEmailSender


logger = logging.getLogger(__name__)


class N8nEmailSender(IEmailSender):
    def __init__(self, *, webhook_url: str, timeout_s: float = 30.0) -> None:
        self._webhook_url = webhook_url
        self._timeout_s = timeout_s

    async def send_book(
        self,
        *,
        bucket: str,
        file_key: str,
        to: str,
        subject: str,
        text: str,
    ) -> EmailSendResult:
        import httpx

        payload = {
            "bucket": bucket,
            "file_key": file_key,
            "to": to,
            "subject": subject,
            "text": text,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                response = await client.post(self._webhook_url, json=payload)
        except httpx.HTTPError as ex:
            # Сети до n8n нет вовсе — структурного ответа не существует.
            logger.exception("n8n email webhook недоступен (url=%s)", self._webhook_url)
            raise EmailSendError("Сервис отправки писем недоступен") from ex

        ok = 200 <= response.status_code < 300

        provider_response: dict[str, object] | None
        try:
            parsed = response.json()
        except ValueError:
            parsed = None
        provider_response = parsed if isinstance(parsed, dict) else None

        if provider_response is not None and isinstance(provider_response.get("message"), str):
            detail = provider_response["message"]
        elif ok:
            detail = "Книга отправлена на e-mail"
        else:
            detail = f"n8n вернул ошибку: HTTP {response.status_code}"

        if not ok:
            logger.error(
                "n8n email webhook вернул ошибку (url=%s status=%s body=%s)",
                self._webhook_url,
                response.status_code,
                response.text,
            )

        return EmailSendResult(
            ok=ok,
            status_code=response.status_code,
            provider_response=provider_response,
            detail=detail,
        )
