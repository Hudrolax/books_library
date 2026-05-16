from __future__ import annotations

from typing import Protocol


class IEmailSender(Protocol):
    async def send_book(
        self,
        *,
        bucket: str,
        file_key: str,
        to: str,
        subject: str,
        text: str,
    ) -> str: ...
