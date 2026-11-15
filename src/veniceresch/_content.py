"""Response-body inspection shared by the client helpers and resources.

Two symmetric guards for 2xx bodies whose shape doesn't match the request:

* :func:`_guard_binary_content_type` — a binary request got a textual body.
* :func:`_parse_json_body` — a JSON request got a body that isn't JSON.

Both raise :class:`~veniceresch._errors.VeniceUnexpectedContentTypeError`.
Kept out of ``_client.py`` so resources (which import the client only under
``TYPE_CHECKING``) can use them at runtime without a circular import.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from veniceresch._errors import VeniceUnexpectedContentTypeError


def _is_textual_content_type(main_type: str) -> bool:
    """True for content types that are text, not binary media.

    Any ``text/*`` plus the XML family. JSON is handled separately because it
    carries a more specific hint (VPS-backed video download_url).
    """
    return main_type.startswith("text/") or main_type in (
        "application/xml",
        "application/xhtml+xml",
    )


def _request_accepts(request: httpx.Request | None, main_type: str) -> bool:
    """True if the request's ``Accept`` header advertised this content type.

    A 2xx body whose media type matches what the caller explicitly asked for is
    by definition not "unexpected", so the binary guard lets it through — even
    when it is textual (e.g. ``augment.parse_text`` asks for ``text/plain``).
    This is the rule the old per-endpoint ``allowed_content_types`` allow-list
    only gestured at; honoring ``Accept`` captures it once for every caller.
    Supports ``*/*`` and ``type/*`` wildcards.
    """
    if request is None or not main_type:
        return False
    accept = request.headers.get("accept", "")
    if not accept:
        return False
    accepted = {part.split(";", 1)[0].strip().lower() for part in accept.split(",")}
    accepted.discard("")
    if "*/*" in accepted or main_type in accepted:
        return True
    top = main_type.split("/", 1)[0]
    return f"{top}/*" in accepted


def _guard_binary_content_type(response: httpx.Response) -> None:
    """Raise if a binary request got a textual 2xx body instead of media bytes.

    Venice's VPS-backed video models answer ``/video/retrieve`` with a JSON
    status object even when ``Accept: video/mp4`` was sent. Other textual 2xx
    bodies (a CDN error page, an auth-proxy interstitial, a presigned-URL error)
    are the same class of silent corruption: without this guard they would be
    returned verbatim as ``bytes``. Genuine media (``video/mp4``, ``image/png``,
    ``application/octet-stream``, …) and untyped/empty responses pass through
    untouched.

    A textual body whose content type the caller *asked for* via ``Accept`` (see
    :func:`_request_accepts`) is not a corruption signal and passes through. To
    let a new binary endpoint return text, advertise that type in its ``Accept``
    header rather than special-casing it here. Opaque downloads that are not a
    Venice API surface (presigned object-store URLs) skip this guard entirely —
    see ``_request_bytes(..., guard_content_type=False)``.
    """
    main_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if not main_type:
        return
    if _request_accepts(response.request, main_type):
        return
    if main_type == "application/json":
        try:
            parsed: Any = response.json()
        except (json.JSONDecodeError, ValueError):
            parsed = response.text
        raise VeniceUnexpectedContentTypeError(
            "Expected binary media but Venice returned a JSON body "
            f"(Content-Type: {main_type!r}). For VPS-backed video models the "
            "media lives at the response's download_url; call video.download(...) "
            "instead of retrieve_binary(...).",
            status_code=response.status_code,
            error_body=parsed if isinstance(parsed, dict) else str(parsed),
            content_type=main_type,
            request=response.request,
            response=response,
        )
    if _is_textual_content_type(main_type):
        raise VeniceUnexpectedContentTypeError(
            "Expected binary media but the response carried a textual body "
            f"(Content-Type: {main_type!r}). This is typically a CDN error page, "
            "an auth-proxy interstitial, or a presigned-URL error returned with a "
            "2xx status — not media bytes.",
            status_code=response.status_code,
            error_body=response.text,
            content_type=main_type,
            request=response.request,
            response=response,
        )


_ERROR_BODY_TEXT_LIMIT = 2048


def _parse_json_body(response: httpx.Response, path: str) -> Any:
    """Decode a 2xx body as JSON, or raise a typed error if it isn't JSON.

    The inverse of :func:`_guard_binary_content_type`: a JSON request got a body
    that cannot be decoded as JSON. Venice's direct-bytes video models answer
    ``/video/retrieve`` with the finished MP4 once a job completes, which
    ``response.json()`` would otherwise surface as a bare ``UnicodeDecodeError``
    (MP4's ``00 00 00 xx ftyp`` header sniffs as UTF-32). A CDN error page
    served with a 2xx would leak a bare ``JSONDecodeError`` the same way.

    Detection is by parse failure, not by ``Content-Type``: valid JSON under an
    odd or missing content type keeps working. ``error_body`` holds truncated
    text for textual bodies and a short descriptor for binary ones; the raw
    bytes stay on ``exc.response.content``.
    """
    try:
        return response.json()
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError both subclass it
        raw_type = response.headers.get("content-type", "")
        main_type = raw_type.split(";", 1)[0].strip().lower()
        size = len(response.content)
        error_body = _describe_undecodable_body(response, main_type)
        message = (
            f"Expected a JSON body from {path} but could not decode it "
            f"(Content-Type: {main_type or 'none'!r}, {size} bytes)."
        )
        if main_type.startswith(("video/", "audio/")) or _looks_like_mp4(response.content):
            message += (
                " Direct-bytes media models return the finished file here; "
                "use video.download(...) / retrieve_binary(...) to fetch it."
            )
        raise VeniceUnexpectedContentTypeError(
            message,
            status_code=response.status_code,
            error_body=error_body,
            content_type=main_type or None,
            request=response.request,
            response=response,
        ) from exc


def _looks_like_mp4(content: bytes) -> bool:
    """True for an ISO base-media file (MP4/MOV/M4A): ``ftyp`` box at offset 4."""
    return content[4:8] == b"ftyp"


_AUDIO_MAGIC = (b"ID3", b"RIFF", b"fLaC", b"OggS")


def _looks_like_audio(content: bytes) -> bool:
    """True for common audio containers: ID3/MP3 frame sync, WAV, FLAC, Ogg, M4A."""
    if content.startswith(_AUDIO_MAGIC) or _looks_like_mp4(content):
        return True
    # bare MPEG audio frame sync (11 set bits); exclude the UTF-16 LE BOM (FF FE)
    return (
        len(content) >= 2
        and content[0] == 0xFF
        and content[1] & 0xE0 == 0xE0
        and content[1] != 0xFE
    )


def _retrieve_body(response: httpx.Response, path: str, kind: str) -> Any:
    """Body of a job-polling ``retrieve``: finished media bytes, or decoded JSON.

    Venice's queue endpoints (``/video/retrieve``, ``/audio/retrieve``) answer
    with a JSON status while the job runs. Some models (direct-bytes video,
    ``elevenlabs-tts-*`` audio) answer with the finished file itself once it
    completes, whatever ``Accept`` says. A non-empty body is treated as media
    when its content type is ``{kind}/*`` or ``application/octet-stream``, or
    when its leading bytes are a known container signature (covers a
    mislabeled body). Returns ``bytes`` for media; anything else goes through
    :func:`_parse_json_body`, so non-JSON text (a CDN page) still raises
    :class:`~veniceresch._errors.VeniceUnexpectedContentTypeError`.
    """
    content = response.content
    main_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    sniff = _looks_like_mp4 if kind == "video" else _looks_like_audio
    if content and (
        main_type.startswith(f"{kind}/")
        or main_type == "application/octet-stream"
        or sniff(content)
    ):
        return content
    return _parse_json_body(response, path)


def _describe_undecodable_body(response: httpx.Response, main_type: str) -> str:
    size = len(response.content)
    if size == 0:
        return "<empty body>"
    textual = main_type in ("", "application/json") or _is_textual_content_type(main_type)
    if textual and not _looks_like_mp4(response.content):
        try:
            text = response.content.decode(response.encoding or "utf-8")
        except (UnicodeDecodeError, LookupError):
            text = None
        if text is not None:
            if len(text) > _ERROR_BODY_TEXT_LIMIT:
                return text[:_ERROR_BODY_TEXT_LIMIT] + f"… [truncated, {size} bytes total]"
            return text
    return f"<{size} bytes of {main_type or 'unknown content type'}>"
