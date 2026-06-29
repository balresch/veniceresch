"""Tests for the augment resource (scrape, search, text-parser)."""

from __future__ import annotations

import io
import json

import pytest

from veniceresch import VeniceRateLimitError, VeniceUnexpectedContentTypeError


async def test_scrape(mock_api, async_client):
    route = mock_api.post("/augment/scrape").respond(
        200,
        json={"url": "https://x", "content": "hi", "format": "markdown"},
    )
    result = await async_client.augment.scrape(url="https://x")
    body = json.loads(route.calls.last.request.content)
    assert body == {"url": "https://x"}
    assert result.url == "https://x"
    assert result.content == "hi"


async def test_search_defaults(mock_api, async_client):
    route = mock_api.post("/augment/search").respond(
        200,
        json={"query": "venice", "results": []},
    )
    await async_client.augment.search(query="venice")
    body = json.loads(route.calls.last.request.content)
    assert body == {"query": "venice"}


async def test_search_with_options(mock_api, async_client):
    route = mock_api.post("/augment/search").respond(
        200,
        json={
            "query": "venice",
            "results": [
                {"title": "t", "url": "u", "content": "c", "date": "d"},
            ],
        },
    )
    result = await async_client.augment.search(
        query="venice",
        limit=5,
        search_provider="google",
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {"query": "venice", "limit": 5, "search_provider": "google"}
    assert result.query == "venice"
    # model_construct keeps nested items as dicts; parse explicitly if you
    # want the strict Result shape.
    assert result.results[0]["title"] == "t"


async def test_parse_posts_multipart_with_json_format(mock_api, async_client):
    route = mock_api.post("/augment/text-parser").respond(
        200,
        json={"text": "parsed body", "tokens": 42},
    )
    result = await async_client.augment.parse(file=b"raw bytes")
    assert route.called
    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    raw = request.content
    assert b'name="file"' in raw
    assert b"raw bytes" in raw
    assert b'name="response_format"' in raw
    assert b"json" in raw
    assert result.text == "parsed body"
    assert result.tokens == 42


async def test_parse_text_returns_string_and_sets_accept(mock_api, async_client):
    route = mock_api.post("/augment/text-parser").respond(
        200,
        text="plain body",
        content_type="text/plain",
    )
    result = await async_client.augment.parse_text(file=b"doc")
    assert isinstance(result, str)
    assert result == "plain body"
    request = route.calls.last.request
    assert request.headers["accept"] == "text/plain"
    raw = request.content
    assert b'name="response_format"' in raw
    assert b"text" in raw


async def test_parse_text_raises_on_unexpected_textual_body(mock_api, async_client):
    # parse_text only advertises Accept: text/plain, so the binary guard treats a
    # text/html body (e.g. an auth-proxy interstitial) as unexpected and surfaces
    # it loudly rather than decoding it as document text.
    mock_api.post("/augment/text-parser").respond(
        200, content=b"<html>login</html>", headers={"content-type": "text/html"}
    )
    with pytest.raises(VeniceUnexpectedContentTypeError):
        await async_client.augment.parse_text(file=b"doc")


def test_sync_parse_text_returns_string(mock_api, sync_client):
    route = mock_api.post("/augment/text-parser").respond(
        200, text="plain body", content_type="text/plain"
    )
    result = sync_client.augment.parse_text(file=b"doc")
    assert result == "plain body"
    assert route.calls.last.request.headers["accept"] == "text/plain"


async def test_parse_accepts_path(mock_api, async_client, tmp_path):
    f = tmp_path / "doc.txt"
    f.write_bytes(b"hello")
    route = mock_api.post("/augment/text-parser").respond(
        200,
        json={"text": "hello parsed", "tokens": 1},
    )
    await async_client.augment.parse(file=f)
    raw = route.calls.last.request.content
    assert b'filename="doc.txt"' in raw
    assert b"hello" in raw


async def test_parse_accepts_string_path(mock_api, async_client, tmp_path):
    f = tmp_path / "report.pdf"
    f.write_bytes(b"PDFBODY")
    route = mock_api.post("/augment/text-parser").respond(200, json={"text": "t", "tokens": 1})
    await async_client.augment.parse(file=str(f))
    raw = route.calls.last.request.content
    assert b'filename="report.pdf"' in raw
    assert b"PDFBODY" in raw


async def test_parse_accepts_file_like(mock_api, async_client):
    route = mock_api.post("/augment/text-parser").respond(200, json={"text": "t", "tokens": 1})
    handle = io.BytesIO(b"DOCSTREAM")
    await async_client.augment.parse(file=handle)
    raw = route.calls.last.request.content
    assert b'filename="document.bin"' in raw  # BytesIO has no usable name
    assert b"DOCSTREAM" in raw
    assert not handle.closed


async def test_parse_missing_path_raises(async_client, tmp_path):
    with pytest.raises(FileNotFoundError):
        await async_client.augment.parse(file=tmp_path / "missing.pdf")


def test_sync_parse_accepts_file_like(mock_api, sync_client):
    route = mock_api.post("/augment/text-parser").respond(200, json={"text": "t", "tokens": 1})
    handle = io.BytesIO(b"SYNCDOC")
    sync_client.augment.parse(file=handle)
    assert b"SYNCDOC" in route.calls.last.request.content
    assert not handle.closed


async def test_search_raises_rate_limit(mock_api, async_client):
    mock_api.post("/augment/search").respond(429, json={"error": "slow down"})
    with pytest.raises(VeniceRateLimitError):
        await async_client.augment.search(query="x")


def test_sync_scrape(mock_api, sync_client):
    mock_api.post("/augment/scrape").respond(
        200,
        json={"url": "https://x", "content": "c", "format": "markdown"},
    )
    result = sync_client.augment.scrape(url="https://x")
    assert result.url == "https://x"
    assert result.content == "c"


# ---- model_construct drift tolerance --------------------------------------
# scrape/search build their wrappers with model_construct, not model_validate
# (see the why-comments in augment.py). These pin the exact drift they tolerate:
# a body the generated schema would reject still round-trips its present fields.


async def test_scrape_tolerates_missing_required_field(mock_api, async_client):
    from pydantic import ValidationError

    from veniceresch.types import WebScrapeResponse

    # Venice drops the schema-required ``format`` field.
    raw = {"url": "https://x", "content": "hi"}
    # Sanity-check that this body is exactly what model_validate would reject —
    # so the test fails loudly if the schema ever stops requiring ``format``.
    with pytest.raises(ValidationError):
        WebScrapeResponse.model_validate(raw)

    mock_api.post("/augment/scrape").respond(200, json=raw)
    result = await async_client.augment.scrape(url="https://x")
    assert result.url == "https://x"
    assert result.content == "hi"


async def test_search_tolerates_invalid_nested_result(mock_api, async_client):
    from pydantic import ValidationError

    from veniceresch.types import WebSearchResponse

    # Nested result is missing the schema-required ``date`` field.
    raw = {"query": "q", "results": [{"title": "t", "url": "u", "content": "c"}]}
    with pytest.raises(ValidationError):
        WebSearchResponse.model_validate(raw)

    mock_api.post("/augment/search").respond(200, json=raw)
    result = await async_client.augment.search(query="q")
    assert result.query == "q"
    # model_construct keeps nested items as the raw dict — no recursive validation.
    assert result.results[0] == {"title": "t", "url": "u", "content": "c"}
