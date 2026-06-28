"""``/augment/*`` resource: web scrape, web search, and document parsing.

``scrape`` and ``search`` are plain JSON POSTs. ``parse`` / ``parse_text``
post a multipart file upload (same shape as :meth:`AsyncAudioResource.transcribe`)
and differ only in which ``response_format`` they send and what they
return — JSON (``TextParserResponse``) vs plain text (``str``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from veniceresch.resources._uploads import UploadInput, open_upload
from veniceresch.types import (
    TextParserResponse,
    WebScrapeResponse,
    WebSearchResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


# bytes | str | Path | binary file-like object. See ``_uploads.open_upload``.
AugmentInput = UploadInput


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class AsyncAugmentResource:
    """Async augment resource. Accessed via ``client.augment``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def scrape(self, *, url: str, **extra: Any) -> WebScrapeResponse:
        body = _drop_none({"url": url, **extra})
        raw = await self._client._request_json("POST", "/augment/scrape", json_body=body)
        # model_construct, not model_validate: Venice has shipped scrape bodies
        # that omit/rename schema-required fields (e.g. ``format``). Bypassing
        # validation keeps drift from raising; unknown fields land on
        # ``model_extra`` via ``extra="allow"``. See CLAUDE.md "Response-model
        # strategy".
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
        # model_construct, not model_validate: tolerate Venice dropping/renaming
        # schema-required fields and keep nested ``results`` as raw dicts (no
        # recursive validation). See CLAUDE.md "Response-model strategy".
        return WebSearchResponse.model_construct(**raw)

    async def parse(self, *, file: AugmentInput, **extra: Any) -> TextParserResponse:
        """Parse a document and return the JSON form (``{text, tokens}``).

        ``file`` may be raw ``bytes``, a path (``str`` / :class:`~pathlib.Path`,
        streamed), or a binary file-like object (streamed; you keep ownership).
        """
        form = {"response_format": "json"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        with open_upload(file, default_name="document.bin") as file_tuple:
            raw = await self._client._request_json(
                "POST",
                "/augment/text-parser",
                files={"file": file_tuple},
                data=form,
            )
        return TextParserResponse.model_validate(raw)

    async def parse_text(self, *, file: AugmentInput, **extra: Any) -> str:
        """Parse a document and return the raw text body (``text/plain``).

        ``file`` accepts the same forms as :meth:`parse`.
        """
        form = {"response_format": "text"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        with open_upload(file, default_name="document.bin") as file_tuple:
            raw = await self._client._request_bytes(
                "POST",
                "/augment/text-parser",
                files={"file": file_tuple},
                data=form,
                headers={"Accept": "text/plain"},
                allowed_content_types=("text/plain",),
            )
        return raw.decode("utf-8")


class AugmentResource:
    """Sync augment resource. Accessed via ``client.augment``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def scrape(self, *, url: str, **extra: Any) -> WebScrapeResponse:
        body = _drop_none({"url": url, **extra})
        raw = self._client._request_json("POST", "/augment/scrape", json_body=body)
        # model_construct, not model_validate: Venice has shipped scrape bodies
        # that omit/rename schema-required fields (e.g. ``format``). Bypassing
        # validation keeps drift from raising; unknown fields land on
        # ``model_extra`` via ``extra="allow"``. See CLAUDE.md "Response-model
        # strategy".
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
        # model_construct, not model_validate: tolerate Venice dropping/renaming
        # schema-required fields and keep nested ``results`` as raw dicts (no
        # recursive validation). See CLAUDE.md "Response-model strategy".
        return WebSearchResponse.model_construct(**raw)

    def parse(self, *, file: AugmentInput, **extra: Any) -> TextParserResponse:
        """Sync mirror of :meth:`AsyncAugmentResource.parse`."""
        form = {"response_format": "json"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        with open_upload(file, default_name="document.bin") as file_tuple:
            raw = self._client._request_json(
                "POST",
                "/augment/text-parser",
                files={"file": file_tuple},
                data=form,
            )
        return TextParserResponse.model_validate(raw)

    def parse_text(self, *, file: AugmentInput, **extra: Any) -> str:
        """Sync mirror of :meth:`AsyncAugmentResource.parse_text`."""
        form = {"response_format": "text"}
        form.update({k: str(v) for k, v in extra.items() if v is not None})
        with open_upload(file, default_name="document.bin") as file_tuple:
            raw = self._client._request_bytes(
                "POST",
                "/augment/text-parser",
                files={"file": file_tuple},
                data=form,
                headers={"Accept": "text/plain"},
                allowed_content_types=("text/plain",),
            )
        return raw.decode("utf-8")


__all__ = ["AsyncAugmentResource", "AugmentResource"]
