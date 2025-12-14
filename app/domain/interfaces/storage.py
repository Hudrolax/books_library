from __future__ import annotations

from pathlib import Path
from typing import Protocol


class IFileStorage(Protocol):
    async def file_exists(self, *, key: str) -> bool: ...

    async def upload_file(
        self,
        *,
        key: str,
        path: Path,
        content_type: str | None = None,
    ) -> None: ...
