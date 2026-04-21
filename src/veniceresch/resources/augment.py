"""``/augment/*`` resource: web scrape, web search, and document parsing.

``scrape`` and ``search`` are plain JSON POSTs. ``parse`` / ``parse_text``
post a multipart file upload (same shape as :meth:`AsyncAudioResource.transcribe`)
and differ only in which ``response_format`` they send and what they
return — JSON (``TextParserResponse``) vs plain text (``str``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from veniceresch.types import (
    TextParserResponse,
    WebScrapeResponse,
    WebSearchResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


AugmentInput = bytes | str | Path


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _augment_file_tuple(file: AugmentInput) -> tuple[str, bytes, str]:
    """Build a (filename, bytes, content-type) tuple for multipart upload."""
    if isinstance(file, bytes):
        return ("document.bin", file, "application/octet-stream")
    if isinstance(file, Path):
        return (file.name, file.read_bytes(), "application/octet-stream")
    p = Path(file)
    return (p.name, p.read_bytes(), "application/octet-stream")


class AsyncAugmentResource:
    """Async augment resource. Accessed via ``client.augment``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def scrape(self, *, url: str, **extra: Any) -> WebScrapeResponse:
        body = _drop_none({"url": url, **extra})
        raw = await self._client._request_json("POST", "/augment/scrape", json_body=body)
        return WebScrapeResponse.model_construct(**raw)

    async def search(
        self,
        *,
        query: str,
        limit: int | None = None,
        search_provider: str | None = None,
        **extra: Any,
    ) -> WebSearchResponse:
        body = _drop_none(
            {
                "query": query,
                "limit": limit,
                "search_provider": search_provider,
                **extra,
            }
        )
        raw = await self._client._request_json("POST", "/augment/search", json_body=body)
        return WebSearchResponse.model_construct(**raw)

    async def parse(self, *, file: AugmentInput, **extra: Any) -> TextParserResponse:
        """Parse a document and return the JSON form (``{text, tokens}``)."""
        files = {"file": _augment_file_tuple(file)}
        form = {"response_format": "json"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        raw = await self._client._request_json(
            "POST",
            "/augment/text-parser",
            files=files,
            data=form,
        )
        return TextParserResponse.model_validate(raw)

    async def parse_text(self, *, file: AugmentInput, **extra: Any) -> str:
        """Parse a document and return the raw text body (``text/plain``)."""
        files = {"file": _augment_file_tuple(file)}
        form = {"response_format": "text"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        raw = await self._client._request_bytes(
            "POST",
            "/augment/text-parser",
            files=files,
            data=form,
            headers={"Accept": "text/plain"},
        )
        return raw.decode("utf-8")


class AugmentResource:
    """Sync augment resource. Accessed via ``client.augment``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def scrape(self, *, url: str, **extra: Any) -> WebScrapeResponse:
        body = _drop_none({"url": url, **extra})
        raw = self._client._request_json("POST", "/augment/scrape", json_body=body)
        return WebScrapeResponse.model_construct(**raw)

    def search(
        self,
        *,
        query: str,
        limit: int | None = None,
        search_provider: str | None = None,
        **extra: Any,
    ) -> WebSearchResponse:
        body = _drop_none(
            {
                "query": query,
                "limit": limit,
                "search_provider": search_provider,
                **extra,
            }
        )
        raw = self._client._request_json("POST", "/augment/search", json_body=body)
        return WebSearchResponse.model_construct(**raw)

    def parse(self, *, file: AugmentInput, **extra: Any) -> TextParserResponse:
        files = {"file": _augment_file_tuple(file)}
        form = {"response_format": "json"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        raw = self._client._request_json(
            "POST",
            "/augment/text-parser",
            files=files,
            data=form,
        )
        return TextParserResponse.model_validate(raw)

    def parse_text(self, *, file: AugmentInput, **extra: Any) -> str:
        files = {"file": _augment_file_tuple(file)}
        form = {"response_format": "text"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        raw = self._client._request_bytes(
            "POST",
            "/augment/text-parser",
            files=files,
            data=form,
            headers={"Accept": "text/plain"},
        )
        return raw.decode("utf-8")


__all__ = ["AsyncAugmentResource", "AugmentResource"]
