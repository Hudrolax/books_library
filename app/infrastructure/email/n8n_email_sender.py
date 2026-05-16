from __future__ import annotations

import logging

from domain.exceptions import EmailSendError
from domain.interfaces.email_sender import IEmailSender


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
    ) -> str:
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
            logger.exception("n8n email webhook недоступен (url=%s)", self._webhook_url)
            raise EmailSendError("Сервис отправки писем недоступен") from ex

        if response.status_code >= 400:
            logger.error(
                "n8n email webhook вернул ошибку (url=%s status=%s body=%s)",
                self._webhook_url,
                response.status_code,
                response.text,
            )
            raise EmailSendError(f"Сервис отправки писем вернул ошибку: HTTP {response.status_code}")

        try:
            message = str(response.json().get("message") or "")
        except ValueError:
            message = response.text

        return message or "Книга отправлена на e-mail"
