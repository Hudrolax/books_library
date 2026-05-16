from __future__ import annotations

from typing import Any, Protocol, TypedDict


class EmailSendResult(TypedDict):
    ok: bool
    status_code: int
    provider_response: dict[str, Any] | None
    detail: str


class IEmailSender(Protocol):
    async def send_book(
        self,
        *,
        bucket: str,
        file_key: str,
        to: str,
        subject: str,
        text: str,
    ) -> EmailSendResult: ...
