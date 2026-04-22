"""Public response types.

Two kinds of types live here:

1. **Hand-authored response shapes** for endpoints where the Venice OpenAPI
   spec defines the response inline (i.e. no named schema), so the
   generator can't emit a top-level class. Those are written out here as
   subclasses of :class:`VeniceBaseModel` so they inherit ``extra=allow``.

2. **Re-exports** of generated classes from :mod:`veniceresch._generated`
   that resource methods return — so callers can
   ``from veniceresch.types import BillingBalanceResponse`` without
   reaching into the generated module.

All models tolerate unknown fields via the shared base class — Venice adds
fields to responses frequently; new fields won't raise
``ValidationError``, they'll just be stored on ``__pydantic_extra__``.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from veniceresch._base_model import VeniceBaseModel
from veniceresch._generated import (
    BillingBalanceResponse,
    BillingUsageAnalyticsResponse,
    BillingUsageResponse,
    ModelCompatibilitySchema,
    ModelResponse,
    ModelTraitSchema,
    ResponsesResponse,
    SimpleGenerateImageRequest,
    WebScrapeRequest,
    WebScrapeResponse,
    WebSearchRequest,
    WebSearchResponse,
)

# Rationale for the hand-written wrappers below:
#
# The list-wrapper endpoints (/models, /models/traits, /image/styles, etc.)
# aren't described by a named response schema in Venice's swagger, so
# datamodel-codegen can't emit a class for them. We define them here.
#
# Inside the wrappers, the ``data`` fields are deliberately typed as ``list``
# or ``dict`` of ``Any`` — NOT as the strict generated schemas (``ModelResponse``,
# ``ModelTraitSchema``, etc.). Pydantic validates recursively, so nesting a
# strict schema inside a tolerant wrapper reintroduces the fragility we're
# trying to avoid — a single unexpected field on a nested model would raise
# ``ValidationError`` and break the whole response. Callers who need the
# nested strict shape can still parse any element: ``ModelResponse.model_validate(item)``.

# ---- chat ----------------------------------------------------------------


class ChatCompletionResponse(VeniceBaseModel):
    """Non-streaming response from ``POST /chat/completions``.

    Swagger describes this inline; fields here are the stable OpenAI-shaped
    ones. Venice-specific extras (e.g. ``venice_parameters`` echoes,
    reasoning blocks) pass through via ``extra="allow"``.
    """

    id: str | None = None
    object: str | None = None
    created: int | None = None
    model: str | None = None
    choices: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] | None = None


class ChatCompletionChunk(VeniceBaseModel):
    """Single SSE event from ``POST /chat/completions`` with ``stream=true``.

    Each ``choice`` has a ``delta`` (OpenAI shape). Tool-call deltas and
    Venice-specific fields pass through unchanged.
    """

    id: str | None = None
    object: str | None = None
    created: int | None = None
    model: str | None = None
    choices: list[dict[str, Any]] = Field(default_factory=list)


# ---- responses -----------------------------------------------------------


class ResponsesChunk(VeniceBaseModel):
    """Single SSE event from ``POST /responses`` with ``stream=true``.

    Venice's swagger documents SSE support on this endpoint but does not
    define a per-chunk schema. The fields below are the stable identifier
    fields from the non-streaming :class:`ResponsesResponse`; everything
    else (deltas, per-block events, ``output_index``, ``sequence_number``,
    …) lands on ``.model_extra`` via ``extra="allow"``. Access unknown
    fields with ``chunk.model_extra`` or ``chunk.model_dump()``.
    """

    id: str | None = None
    object: str | None = None
    created_at: int | None = None
    model: str | None = None


# ---- models --------------------------------------------------------------


class ModelList(VeniceBaseModel):
    """Response from ``GET /models``.

    Each entry in ``data`` is a model dict with the shape of
    :class:`ModelResponse` — left as ``dict[str, Any]`` here for drift
    tolerance. Call :meth:`parsed_data` for the typed form, or parse a
    single entry via ``ModelResponse.model_validate(result.data[0])``.
    """

    data: list[dict[str, Any]] = Field(default_factory=list)
    object: str | None = None
    type: str | None = None

    def parsed_data(self) -> list[ModelResponse]:
        """Return ``.data`` elements as typed :class:`ModelResponse` objects.

        Uses ``model_construct`` so unknown fields land on
        ``.model_extra`` rather than raising — drift-tolerant with
        attribute access on the known fields.
        """
        return [ModelResponse.model_construct(**item) for item in self.data]


class ModelTraitsResponse(VeniceBaseModel):
    """Response from ``GET /models/traits``.

    ``data`` is a ``{trait_name: model_id}`` mapping in the wild. See
    :class:`ModelTraitSchema` for the typed form.
    """

    data: dict[str, Any] | None = None
    object: str | None = None
    type: str | None = None


class ModelCompatibilityResponse(VeniceBaseModel):
    """Response from ``GET /models/compatibility_mapping``.

    ``data`` is a mapping from OpenAI model id to Venice model id. See
    :class:`ModelCompatibilitySchema` for the typed form.
    """

    data: dict[str, Any] | None = None
    object: str | None = None
    type: str | None = None


# ---- image ---------------------------------------------------------------


class ImageStylesResponse(VeniceBaseModel):
    """Response from ``GET /image/styles``."""

    data: list[str] = Field(default_factory=list)
    object: str | None = None


class GenerateImageResponse(VeniceBaseModel):
    """JSON response from ``POST /image/generate`` (when ``return_binary`` is false).

    For raw bytes, use :meth:`veniceresch.resources.image.AsyncImageResource.generate_binary`.
    """

    id: str | None = None
    images: Annotated[
        list[str],
        Field(description="Base64-encoded image data, one entry per image."),
    ] = Field(default_factory=list)
    request: dict[str, Any] | None = None
    timing: dict[str, Any] | None = None


class OpenAIImageResponse(VeniceBaseModel):
    """Response from ``POST /images/generations`` (OpenAI-compatible alias).

    Each entry in ``data`` is either ``{"b64_json": "..."}`` or
    ``{"url": "..."}`` depending on the request's ``response_format``.
    Kept as ``list[dict[str, Any]]`` for drift tolerance; parse
    individual entries explicitly if you need a stricter shape.
    """

    created: int | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


# ---- embeddings ----------------------------------------------------------


class EmbeddingsResponse(VeniceBaseModel):
    """Response from ``POST /embeddings``."""

    data: list[dict[str, Any]] = Field(default_factory=list)
    model: str | None = None
    object: str | None = None
    usage: dict[str, Any] | None = None


# ---- video ---------------------------------------------------------------


class VideoQueueResponse(VeniceBaseModel):
    """Response from ``POST /video/queue``.

    ``download_url`` is present only for VPS-backed models that stream the
    output directly; queue-only models require a follow-up
    :meth:`~veniceresch.resources.video.AsyncVideoResource.retrieve` /
    :meth:`~veniceresch.resources.video.AsyncVideoResource.retrieve_binary`.
    """

    model: str | None = None
    queue_id: str | None = None
    download_url: str | None = None


class VideoRetrieveResponse(VeniceBaseModel):
    """Response from ``POST /video/retrieve`` (JSON form).

    For the binary form (MP4 bytes), use
    :meth:`~veniceresch.resources.video.AsyncVideoResource.retrieve_binary`.
    ``status`` is ``"PROCESSING"`` until the job finishes. Completion
    responses carry additional fields (e.g. ``download_url``) that land
    on ``.model_extra``.
    """

    status: str | None = None
    average_execution_time: float | None = None
    execution_duration: float | None = None


class VideoQuoteResponse(VeniceBaseModel):
    """Response from ``POST /video/quote`` — cost estimate in USD."""

    quote: float | None = None


class VideoCompleteResponse(VeniceBaseModel):
    """Response from ``POST /video/complete``."""

    success: bool | None = None


class VideoTranscriptionResponse(VeniceBaseModel):
    """Response from ``POST /video/transcriptions`` (JSON form)."""

    transcript: str | None = None
    lang: str | None = None


# ---- audio ---------------------------------------------------------------


class AudioQueueResponse(VeniceBaseModel):
    """Response from ``POST /audio/queue``."""

    model: str | None = None
    queue_id: str | None = None
    status: str | None = None


class AudioRetrieveResponse(VeniceBaseModel):
    """Response from ``POST /audio/retrieve`` (JSON form).

    For the binary form (audio/mpeg or audio/wav or audio/flac bytes),
    use
    :meth:`~veniceresch.resources.audio.AsyncAudioResource.retrieve_binary`.
    """

    status: str | None = None
    average_execution_time: float | None = None
    execution_duration: float | None = None


class AudioQuoteResponse(VeniceBaseModel):
    """Response from ``POST /audio/quote`` — cost estimate in USD."""

    quote: float | None = None


class AudioCompleteResponse(VeniceBaseModel):
    """Response from ``POST /audio/complete``."""

    success: bool | None = None


class AudioTranscriptionResponse(VeniceBaseModel):
    """Response from ``POST /audio/transcriptions`` (JSON form).

    ``timestamps`` is a nested dict of per-word / per-segment / per-char
    timing arrays. Kept as ``dict[str, Any]`` for drift tolerance.
    """

    text: str | None = None
    duration: float | None = None
    timestamps: dict[str, Any] | None = None


# ---- augment ------------------------------------------------------------


class TextParserResponse(VeniceBaseModel):
    """JSON response from ``POST /augment/text-parser`` (response_format=json).

    For the plain-text format use
    :meth:`veniceresch.resources.augment.AsyncAugmentResource.parse_text`,
    which returns a ``str`` instead.
    """

    text: str | None = None
    tokens: int | None = None


# ---- characters ---------------------------------------------------------


class CharacterListResponse(VeniceBaseModel):
    """Response from ``GET /characters``.

    Each entry in ``data`` is a character dict. Left as ``dict[str, Any]``
    for drift tolerance — parse individual entries explicitly if you want
    a stricter shape.
    """

    data: list[dict[str, Any]] = Field(default_factory=list)
    object: str | None = None


class CharacterDetailResponse(VeniceBaseModel):
    """Response from ``GET /characters/{slug}``."""

    data: dict[str, Any] | None = None
    object: str | None = None


class CharacterReviewsResponse(VeniceBaseModel):
    """Response from ``GET /characters/{slug}/reviews``.

    ``pagination`` carries ``page``, ``pageSize``, ``total``, ``totalPages``.
    ``summary`` carries ``averageRating`` and ``totalReviews``.
    """

    data: list[dict[str, Any]] = Field(default_factory=list)
    object: str | None = None
    pagination: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None


# ---- api_keys -----------------------------------------------------------


class ApiKeyListResponse(VeniceBaseModel):
    """Response from ``GET /api_keys``.

    Each entry in ``data`` is an API-key summary (id, description,
    ``apiKeyType``, ``last6Chars``, ``createdAt``, ``expiresAt``,
    ``lastUsedAt``, ``consumptionLimits``, optional ``usage`` block).
    """

    data: list[dict[str, Any]] = Field(default_factory=list)
    object: str | None = None


class ApiKeyDetailResponse(VeniceBaseModel):
    """Response from ``GET /api_keys/{id}`` — single key plus usage."""

    data: dict[str, Any] | None = None


class ApiKeyCreateResponse(VeniceBaseModel):
    """Response from ``POST /api_keys``.

    ``data.apiKey`` carries the raw key and is only returned once — save it
    immediately.
    """

    data: dict[str, Any] | None = None
    success: bool | None = None


class ApiKeyUpdateResponse(VeniceBaseModel):
    """Response from ``PATCH /api_keys``."""

    data: dict[str, Any] | None = None
    success: bool | None = None


class ApiKeyDeleteResponse(VeniceBaseModel):
    """Response from ``DELETE /api_keys``."""

    success: bool | None = None


class ApiKeyRateLimitsResponse(VeniceBaseModel):
    """Response from ``GET /api_keys/rate_limits``.

    ``data`` carries ``accessPermitted``, ``apiTier``, ``balances`` (USD
    and DIEM), ``keyExpiration``, ``nextEpochBegins``, and ``rateLimits``
    (a list of ``{apiModelId, rateLimits: [{amount, type}]}`` entries).
    """

    data: dict[str, Any] | None = None


class ApiKeyRateLimitLogsResponse(VeniceBaseModel):
    """Response from ``GET /api_keys/rate_limits/log`` — last 50 exceedances."""

    data: list[dict[str, Any]] = Field(default_factory=list)
    object: str | None = None


class Web3KeyChallengeResponse(VeniceBaseModel):
    """Response from ``GET /api_keys/generate_web3_key``.

    ``data.token`` is the challenge to sign with the wallet's private key
    and pass back to
    :meth:`~veniceresch.resources.api_keys.AsyncApiKeysResource.generate_web3_key`.
    """

    data: dict[str, Any] | None = None
    success: bool | None = None


class Web3KeyCreateResponse(VeniceBaseModel):
    """Response from ``POST /api_keys/generate_web3_key``.

    Same shape as :class:`ApiKeyCreateResponse` — ``data.apiKey`` is the
    raw key and is only returned once.
    """

    data: dict[str, Any] | None = None
    success: bool | None = None


# ---- x402 ---------------------------------------------------------------


class X402BalanceResponse(VeniceBaseModel):
    """Response from ``GET /x402/balance/{walletAddress}``.

    ``data`` carries ``walletAddress``, ``balanceUsd``, ``canConsume``,
    ``minimumTopUpUsd``, ``suggestedTopUpUsd``, and an optional
    ``diemBalanceUsd`` when the wallet is linked to a Venice user.
    """

    success: bool | None = None
    data: dict[str, Any] | None = None


class X402TopUpResponse(VeniceBaseModel):
    """Response from ``POST /x402/top-up`` (success — with valid payment header).

    ``data`` carries ``walletAddress``, ``amountCredited``, ``newBalance``,
    and ``paymentId``. Calling without the ``X-402-Payment`` header raises
    :class:`~veniceresch.VeniceX402PaymentRequiredError` with the discovery
    payload on ``.accepts``.
    """

    success: bool | None = None
    data: dict[str, Any] | None = None


class X402TransactionsResponse(VeniceBaseModel):
    """Response from ``GET /x402/transactions/{walletAddress}``.

    ``data`` carries ``walletAddress``, ``currentBalance``, a
    ``transactions`` list (each with ``id``, ``amount``, ``balanceAfter``,
    ``type``, ``createdAt``, ``requestId``, ``modelId``), and
    ``pagination`` (``limit``, ``offset``, ``hasMore``).
    """

    success: bool | None = None
    data: dict[str, Any] | None = None


__all__ = [
    "ApiKeyCreateResponse",
    "ApiKeyDeleteResponse",
    "ApiKeyDetailResponse",
    "ApiKeyListResponse",
    "ApiKeyRateLimitLogsResponse",
    "ApiKeyRateLimitsResponse",
    "ApiKeyUpdateResponse",
    "AudioCompleteResponse",
    "AudioQueueResponse",
    "AudioQuoteResponse",
    "AudioRetrieveResponse",
    "AudioTranscriptionResponse",
    "BillingBalanceResponse",
    "BillingUsageAnalyticsResponse",
    "BillingUsageResponse",
    "CharacterDetailResponse",
    "CharacterListResponse",
    "CharacterReviewsResponse",
    "ChatCompletionChunk",
    "ChatCompletionResponse",
    "EmbeddingsResponse",
    "GenerateImageResponse",
    "ImageStylesResponse",
    "ModelCompatibilityResponse",
    "ModelCompatibilitySchema",
    "ModelList",
    "ModelResponse",
    "ModelTraitSchema",
    "ModelTraitsResponse",
    "OpenAIImageResponse",
    "ResponsesChunk",
    "ResponsesResponse",
    "SimpleGenerateImageRequest",
    "TextParserResponse",
    "VeniceBaseModel",
    "VideoCompleteResponse",
    "VideoQueueResponse",
    "VideoQuoteResponse",
    "VideoRetrieveResponse",
    "VideoTranscriptionResponse",
    "Web3KeyChallengeResponse",
    "Web3KeyCreateResponse",
    "WebScrapeRequest",
    "WebScrapeResponse",
    "WebSearchRequest",
    "WebSearchResponse",
    "X402BalanceResponse",
    "X402TopUpResponse",
    "X402TransactionsResponse",
]
