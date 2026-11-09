# AUTO-GENERATED from vendor/venice-swagger.yaml. Do not edit by hand.

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel

from veniceresch._base_model import VeniceBaseModel


class StandardError(VeniceBaseModel):
    error: Annotated[str, Field(description="A description of the error")]


class DetailedError(VeniceBaseModel):
    details: Annotated[
        dict[str, Any] | None,
        Field(
            description="Details about the incorrect input",
            examples=[{"_errors": [], "field": {"_errors": ["Field is required"]}}],
        ),
    ] = None
    error: Annotated[str, Field(description="A description of the error")]


class Error(Enum):
    This_API_key_is_restricted_to_configured_IP_addresses__and_this_request_s_source_IP_is_not_allowed = "This API key is restricted to configured IP addresses, and this request's source IP is not allowed"


class ApiKeyIpRestrictedError(VeniceBaseModel):
    error: Annotated[
        Error,
        Field(
            description="A description of the error",
            examples=[
                "This API key is restricted to configured IP addresses, and this request's source IP is not allowed"
            ],
        ),
    ]


class ContentViolationError(VeniceBaseModel):
    error: Annotated[str, Field(description="A description of the error")]
    suggested_prompt: Annotated[
        str | None,
        Field(
            description="An optional provider-suggested replacement prompt that complies with content policy.",
            examples=[
                "A cinematic instrumental track inspired by stormy weather and dramatic tension."
            ],
        ),
    ] = None


class ImageContentViolationError(VeniceBaseModel):
    error: Annotated[str, Field(description="A description of the error")]
    suggested_prompt: Annotated[
        str | None,
        Field(
            description="An optional provider-suggested replacement prompt that complies with content policy.",
            examples=["A watercolor painting of a lighthouse on a rocky coast at sunset."],
        ),
    ] = None
    recommended_model: Annotated[
        str | None,
        Field(
            description="A model ID that can be used as an alternative when a recommendation is available.",
            examples=["chroma"],
        ),
    ] = None
    retryable: Annotated[
        bool | None,
        Field(
            description="Present on every content-policy rejection: whether retrying the same request may succeed. True when the selected model's provider moderation is nondeterministic; false when the same request would be rejected again. Absent on other 422 errors, such as an input image that exceeds the pixel limit.",
            examples=[True],
        ),
    ] = None


class Type(Enum):
    provider_content_policy = "provider_content_policy"


class Error1(VeniceBaseModel):
    message: Annotated[
        str,
        Field(
            description="A human-readable explanation of the provider content policy rejection and the recommended next action.",
            examples=[
                "The selected model provider rejected this request due to its content policies. Credits have been refunded. Try using wan-2-7-text-to-video instead."
            ],
        ),
    ]
    type: Annotated[
        Type,
        Field(
            description="Machine-readable error type for provider content policy rejections.",
            examples=["provider_content_policy"],
        ),
    ]
    recommended_model: Annotated[
        str | None,
        Field(
            description="A model ID that can be used as an alternative when a recommendation is available.",
            examples=["wan-2-7-text-to-video"],
        ),
    ] = None
    credits_refunded: Annotated[
        bool,
        Field(
            description="Whether credits were refunded for the rejected generation.",
            examples=[True],
        ),
    ]


class ProviderContentPolicyError(VeniceBaseModel):
    error: Error1


class Code(Enum):
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"


class PayloadTooLargeError(VeniceBaseModel):
    code: Annotated[
        Code,
        Field(description="Machine-readable error code.", examples=["PAYLOAD_TOO_LARGE"]),
    ]
    error: Annotated[
        str,
        Field(
            description="A description of the error",
            examples=["File exceeds the maximum allowed size of 25 MB."],
        ),
    ]


class Resource(VeniceBaseModel):
    url: Annotated[
        str,
        Field(
            description="Protected resource URL.",
            examples=["https://api.venice.ai/api/v1/chat/completions"],
        ),
    ]
    description: Annotated[
        str,
        Field(description="Human-readable resource description.", examples=["Venice API"]),
    ]
    mimeType: Annotated[
        str, Field(description="Resource MIME type.", examples=["application/json"])
    ]


class Scheme(Enum):
    exact = "exact"


class Accept(VeniceBaseModel):
    scheme: Annotated[Scheme, Field(description="x402 payment scheme.", examples=["exact"])]
    network: Annotated[
        str,
        Field(description="Payment network for this requirement.", examples=["solana"]),
    ]
    asset: Annotated[
        str,
        Field(
            description="USDC token address or mint for the selected network.",
            examples=["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"],
        ),
    ]
    amount: Annotated[
        str,
        Field(
            description="Required payment amount in base units (USDC has 6 decimals).",
            examples=["10000000"],
        ),
    ]
    payTo: Annotated[
        str,
        Field(
            description="Receiver wallet address for the selected network.",
            examples=["8qUL23aSj7mDWdoLMXGHFvnVCT9wd7jXcysiekroADEL"],
        ),
    ]
    maxTimeoutSeconds: Annotated[
        float,
        Field(description="Maximum time allowed for payment settlement.", examples=[300]),
    ]
    extra: Annotated[
        dict[str, Any],
        Field(
            description="Network-specific x402 metadata. Solana requirements include a feePayer.",
            examples=[
                {
                    "name": "USD Coin",
                    "version": "2",
                    "feePayer": "BFK9TLC3edb13K6v4YyH3DwPb5DSUpkWvb7XnqCL9b4F",
                }
            ],
        ),
    ]


class ApiKey(VeniceBaseModel):
    header: Annotated[
        str,
        Field(
            description="API key authentication header format.",
            examples=["Authorization: Bearer YOUR_API_KEY"],
        ),
    ]
    getKey: Annotated[
        str,
        Field(
            description="Where to create or manage API keys.",
            examples=["https://venice.ai/settings/api"],
        ),
    ]
    docs: Annotated[
        str,
        Field(
            description="API key documentation URL.",
            examples=["https://docs.venice.ai/api-reference"],
        ),
    ]


class X402Wallet(VeniceBaseModel):
    header: Annotated[
        str,
        Field(
            description="Header used for Sign-In-With-X wallet authentication.",
            examples=["SIGN-IN-WITH-X"],
        ),
    ]
    legacyHeader: Annotated[
        str,
        Field(
            description="Legacy Sign-In-With-X header accepted during migration.",
            examples=["X-Sign-In-With-X"],
        ),
    ]
    topUp: Annotated[
        str,
        Field(
            description="Endpoint used to discover and submit x402 top-up payments.",
            examples=["POST /api/v1/x402/top-up"],
        ),
    ]
    docs: Annotated[
        str,
        Field(
            description="x402 top-up API documentation URL.",
            examples=["https://docs.venice.ai/api-reference/endpoint/x402/top-up"],
        ),
    ]


class AuthOptions(VeniceBaseModel):
    apiKey: ApiKey
    x402Wallet: X402Wallet


class X402InferencePaymentRequired1(VeniceBaseModel):
    x402Version: Annotated[float, Field(description="x402 protocol version.", examples=[2])]
    error: Annotated[
        str | None,
        Field(
            description="Human-readable payment requirement message.",
            examples=["Payment required"],
        ),
    ] = None
    resource: Resource
    accepts: Annotated[
        list[Accept],
        Field(
            description="Protocol payment requirements. Clients should choose one entry, such as Base or Solana, and sign exactly that requirement."
        ),
    ]
    extensions: Annotated[
        dict[str, Any] | None,
        Field(
            description="Protocol extensions. Inference 402 responses include `sign-in-with-x` with a SIWX challenge for wallet-credit authentication."
        ),
    ] = None
    authOptions: AuthOptions


class Error2(Enum):
    Payment_required = "Payment required"


class Code1(Enum):
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"


class Reason(Enum):
    insufficient_balance = "insufficient_balance"


class TopUpInstructions(VeniceBaseModel):
    step1: Annotated[
        str,
        Field(
            description="First step: get payment requirements.",
            examples=[
                "POST /api/v1/x402/top-up with no payment header to get payment requirements"
            ],
        ),
    ]
    step2: Annotated[
        str,
        Field(
            description="Second step: sign the payment.",
            examples=[
                "Choose a payment option from accepts and sign a USDC transfer authorization using the x402 SDK (createPaymentHeader)"
            ],
        ),
    ]
    step3: Annotated[
        str,
        Field(
            description="Third step: submit the payment.",
            examples=["POST /api/v1/x402/top-up with the signed PAYMENT-SIGNATURE header"],
        ),
    ]
    receiverWallet: Annotated[
        str,
        Field(
            description="Legacy Base receiver wallet address. Prefer the selected accepts entry from /x402/top-up for network-specific payTo values.",
            examples=["<RECEIVER_WALLET_ADDRESS>"],
        ),
    ]
    tokenAddress: Annotated[
        str,
        Field(
            description="Legacy Base USDC token address. Prefer the selected accepts entry from /x402/top-up for network-specific assets.",
            examples=["<USDC_TOKEN_ADDRESS>"],
        ),
    ]
    tokenDecimals: Annotated[float, Field(description="Token decimal places.", examples=[6])]
    network: Annotated[
        str,
        Field(
            description="Legacy Base target network. Prefer the selected accepts entry from /x402/top-up for network-specific values.",
            examples=["eip155:8453"],
        ),
    ]
    minimumAmountUsd: Annotated[
        float, Field(description="Minimum top-up amount in USD.", examples=[5])
    ]


class Info(VeniceBaseModel):
    domain: Annotated[
        str,
        Field(description="Domain for the SIWX challenge.", examples=["api.venice.ai"]),
    ]
    uri: Annotated[
        str,
        Field(
            description="Resource URI for the challenge.",
            examples=["https://api.venice.ai/api/v1/chat/completions"],
        ),
    ]
    version: Annotated[str, Field(description="SIWX version.", examples=["1"])]
    nonce: Annotated[
        str,
        Field(description="Unique nonce for replay protection.", examples=["{{nonce}}"]),
    ]
    issuedAt: Annotated[
        str,
        Field(
            description="ISO timestamp when the challenge was issued.",
            examples=["2026-04-09T12:00:00.000Z"],
        ),
    ]
    expirationTime: Annotated[
        str,
        Field(
            description="ISO timestamp when the challenge expires.",
            examples=["2026-04-09T12:05:00.000Z"],
        ),
    ]
    statement: Annotated[
        str,
        Field(
            description="Human-readable statement for the signature.",
            examples=["Sign in to Venice AI"],
        ),
    ]


class Type1(Enum):
    eip191 = "eip191"
    eip1271 = "eip1271"
    ed25519 = "ed25519"


class SupportedChain(VeniceBaseModel):
    chainId: Annotated[
        str,
        Field(
            description="Supported chain identity.",
            examples=["solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"],
        ),
    ]
    type: Annotated[
        Type1,
        Field(description="Signature type accepted for this chain.", examples=["ed25519"]),
    ]


class SiwxChallenge(VeniceBaseModel):
    info: Info
    supportedChains: Annotated[
        list[SupportedChain],
        Field(description="Supported SIWX chains and signature types."),
    ]


class X402InferencePaymentRequired2(VeniceBaseModel):
    error: Annotated[Error2, Field(description="Error message indicating payment is required.")]
    code: Annotated[Code1, Field(description="Machine-readable error code.")]
    reason: Annotated[
        Reason,
        Field(description="Reason the x402-authenticated request could not proceed."),
    ]
    message: Annotated[
        str | None,
        Field(
            description="Human-readable context about the payment requirement.",
            examples=["Insufficient x402 balance"],
        ),
    ] = None
    currentBalanceUsd: Annotated[
        float | None,
        Field(description="Current x402 credit balance for the wallet.", examples=[0.01]),
    ] = None
    minimumBalanceUsd: Annotated[
        float | None,
        Field(
            description="Minimum x402 credit balance required before the request can run.",
            examples=[0.1],
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(description="Protected resource description.", examples=["Venice API"]),
    ] = None
    suggestedTopUpUsd: Annotated[
        float, Field(description="Suggested amount to top up in USD.", examples=[10])
    ]
    minimumTopUpUsd: Annotated[
        float, Field(description="Minimum allowed top-up amount in USD.", examples=[5])
    ]
    supportedTokens: Annotated[
        list[str],
        Field(
            description="List of supported token symbols for payment.",
            examples=[["USDC"]],
        ),
    ]
    supportedChains: Annotated[
        list[str],
        Field(description="List of supported top-up rails.", examples=[["base", "solana"]]),
    ]
    topUpInstructions: TopUpInstructions
    siwxChallenge: SiwxChallenge


class X402InferencePaymentRequired(
    RootModel[X402InferencePaymentRequired1 | X402InferencePaymentRequired2]
):
    root: X402InferencePaymentRequired1 | X402InferencePaymentRequired2


class Type2(Enum):
    ephemeral = "ephemeral"


class CacheControl(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type2,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type3(Enum):
    text = "text"


class Content(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    text: Annotated[
        str,
        Field(
            description="The prompt text of the message. Must be at-least one character in length",
            examples=["Why is the sky blue?"],
            min_length=1,
            title="Text Content Object",
        ),
    ]
    type: Annotated[Type3, Field(title="Text Content String")]


class Type4(Enum):
    ephemeral = "ephemeral"


class CacheControl1(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type4,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Detail(Enum):
    auto = "auto"
    low = "low"
    high = "high"
    original = "original"


class ImageUrl(VeniceBaseModel):
    detail: Annotated[
        Detail | None,
        Field(
            description="Image detail auto, low, and high are now forwarded to providers rather than ignored. Explicit high detail may increase image-token usage and cost. For plaintext requests, original is preserved on direct OpenAI routes and mapped to high on other routes, including retries. Encrypted E2EE content is unchanged. Unrecognized values are ignored for legacy Chat Completions compatibility."
        ),
    ] = None
    url: Annotated[
        AnyUrl,
        Field(
            description="The URL of the image. Can be a data URL with a base64 encoded image or a public URL. URL must be publicly accessible. Image must pass validation checks and be >= 64 pixels square."
        ),
    ]


class Type5(Enum):
    image_url = "image_url"


class Content1(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl1 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    image_url: Annotated[
        ImageUrl,
        Field(
            description="Object containing the image URL information",
            title="Image URL Object",
        ),
    ]
    type: Type5


class Type6(Enum):
    ephemeral = "ephemeral"


class CacheControl2(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type6,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Format(Enum):
    wav = "wav"
    mp3 = "mp3"
    aiff = "aiff"
    aac = "aac"
    ogg = "ogg"
    flac = "flac"
    m4a = "m4a"
    pcm16 = "pcm16"
    pcm24 = "pcm24"


class InputAudio(VeniceBaseModel):
    data: Annotated[
        str,
        Field(
            description="Base64-encoded audio data. Direct URLs are not supported for audio content."
        ),
    ]
    format: Annotated[
        Format | None,
        Field(
            description="The format of the audio file. Common formats include wav, mp3, aac, ogg, flac, m4a. Defaults to wav.",
            examples=["wav"],
        ),
    ] = "wav"


class Type7(Enum):
    input_audio = "input_audio"


class Content2(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl2 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    input_audio: Annotated[
        InputAudio,
        Field(
            description="Object containing the base64-encoded audio data and format",
            title="Input Audio Object",
        ),
    ]
    type: Type7


class Type8(Enum):
    ephemeral = "ephemeral"


class CacheControl3(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type8,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type9(Enum):
    video_url = "video_url"


class VideoUrl(VeniceBaseModel):
    url: Annotated[
        AnyUrl,
        Field(
            description="The URL of the video. Can be a direct URL (including YouTube links for some providers), or a base64-encoded data URL (e.g., data:video/mp4;base64,...). Supported formats: mp4, mpeg, mov, webm. Remote URLs must be publicly accessible, must not redirect, and must return a permitted video Content-Type. At most 3 videos may be provided in one request."
        ),
    ]


class Content3(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl3 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    type: Type9
    video_url: Annotated[
        VideoUrl,
        Field(
            description="Object containing the video URL information",
            title="Video URL Object",
        ),
    ]


class Type10(Enum):
    ephemeral = "ephemeral"


class CacheControl4(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type10,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type11(Enum):
    file = "file"


class File(VeniceBaseModel):
    file_data: Annotated[
        str,
        Field(
            description="The file content as a data URL (e.g., data:application/pdf;base64,...) or a publicly accessible URL. Supported formats: PDF, EPUB, DOCX, PPTX, XLSX, XLS, plain text, Markdown, CSV, JSON, and most source-code files (e.g., .py, .js, .ts, .c, .cpp, .java, .go, .rs, .ps1, .sh, .yaml, .sql)."
        ),
    ]
    filename: Annotated[
        str | None,
        Field(
            description="Optional filename for the file. Used for display purposes.",
            examples=["document.pdf"],
        ),
    ] = None


class Content4(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl4 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    type: Type11
    file: Annotated[
        File,
        Field(
            description="Object containing the file data and optional filename",
            title="File Object",
        ),
    ]


class Role(Enum):
    user = "user"


class Messages(VeniceBaseModel):
    content: str | list[Content | Content1 | Content2 | Content3 | Content4]
    name: str | None = None
    role: Role


class Type12(Enum):
    ephemeral = "ephemeral"


class CacheControl5(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type12,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class CacheControl6(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type12,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type14(Enum):
    text = "text"


class ContentItem(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl6 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    text: Annotated[
        str,
        Field(
            description="The prompt text of the message. Must be at-least one character in length",
            examples=["Why is the sky blue?"],
            min_length=1,
            title="Text Content Object",
        ),
    ]
    type: Annotated[Type14, Field(title="Text Content String")]


class ReasoningDetail(VeniceBaseModel):
    data: str | None = None
    format: str | None = None
    id: str | None = None
    index: float | None = None
    text: str | None = None
    type: str


class Role1(Enum):
    assistant = "assistant"


class Messages1(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl5 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    content: str | list[ContentItem] | Any | None = None
    name: str | None = None
    reasoning_content: str | None = None
    reasoning_details: Annotated[
        list[ReasoningDetail] | None,
        Field(
            description="Reasoning details returned by certain reasoning models that support this feature (e.g., Gemini 3 Pro). Not all reasoning models return this field. For multi-turn conversations with tool calls on supported models, pass back the reasoning_details exactly as received to preserve thought signatures."
        ),
    ] = None
    role: Role1
    thought_signature: Annotated[
        str | None,
        Field(
            description="Gemini thought signature returned by native GCP transport. For multi-turn conversations (especially with tool calls), pass it back exactly as received to preserve thought signatures."
        ),
    ] = None
    tool_calls: list[Any] | None = None


class Type15(Enum):
    ephemeral = "ephemeral"


class CacheControl7(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type15,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Role2(Enum):
    tool = "tool"


class Messages2(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl7 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    content: str
    name: str | None = None
    reasoning_content: str | None = None
    role: Role2
    tool_call_id: str
    tool_calls: list[Any] | None = None


class CacheControl8(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type15,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type17(Enum):
    text = "text"


class ContentItem1(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl8 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    text: Annotated[
        str,
        Field(
            description="The prompt text of the message. Must be at-least one character in length",
            examples=["Why is the sky blue?"],
            min_length=1,
            title="Text Content Object",
        ),
    ]
    type: Annotated[Type17, Field(title="Text Content String")]


class Role3(Enum):
    system = "system"


class Messages3(VeniceBaseModel):
    content: str | list[ContentItem1]
    name: str | None = None
    role: Role3


class Type18(Enum):
    ephemeral = "ephemeral"


class CacheControl9(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type18,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type19(Enum):
    text = "text"


class ContentItem2(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl9 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    text: Annotated[
        str,
        Field(
            description="The prompt text of the message. Must be at-least one character in length",
            examples=["Why is the sky blue?"],
            min_length=1,
            title="Text Content Object",
        ),
    ]
    type: Annotated[Type19, Field(title="Text Content String")]


class Role4(Enum):
    developer = "developer"


class Messages4(VeniceBaseModel):
    content: str | list[ContentItem2]
    name: str | None = None
    role: Role4


class PromptCacheRetention(Enum):
    default = "default"
    extended = "extended"
    field_24h = "24h"


class Effort(Enum):
    none = "none"
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
    xhigh = "xhigh"
    max = "max"


class Summary(Enum):
    auto = "auto"
    concise = "concise"
    detailed = "detailed"


class Reasoning(VeniceBaseModel):
    effort: Annotated[
        Effort | None,
        Field(
            description="Controls the reasoning effort level for supported models. Higher effort means more thorough reasoning but increased token usage. Defaults to the model configuration if not specified.",
            examples=["medium"],
        ),
    ] = None
    enabled: Annotated[
        bool | None,
        Field(
            description="Set to false to disable reasoning on supported models. Defaults to the model configuration if not specified. Ignored when an effort level is provided.",
            examples=[False],
        ),
    ] = None
    summary: Annotated[
        Summary | None,
        Field(
            description='Controls whether and how the model generates a summary of its reasoning. "auto" lets the model decide, "concise" requests a brief summary, "detailed" requests a thorough summary.',
            examples=["auto"],
        ),
    ] = None


class ReasoningEffort(Enum):
    none = "none"
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
    xhigh = "xhigh"
    max = "max"


class Stop(RootModel[list[str]]):
    root: Annotated[
        list[str],
        Field(
            description="Up to 4 sequences where the API will stop generating further tokens. Defaults to null.",
            max_length=4,
            min_length=1,
            title="Array of Strings",
        ),
    ]


class StreamOptions(VeniceBaseModel):
    include_usage: Annotated[
        bool | None,
        Field(description="Whether to include usage information in the stream."),
    ] = None


class Fallback(VeniceBaseModel):
    model: str


class Verbosity(Enum):
    low = "low"
    medium = "medium"
    high = "high"
    auto = "auto"


class Text(VeniceBaseModel):
    verbosity: Annotated[
        Verbosity | None,
        Field(description="Controls the verbosity of the text response.", examples=["low"]),
    ] = None


class EnableWebSearch(Enum):
    auto = "auto"
    off = "off"
    on = "on"


class VeniceParameters(VeniceBaseModel):
    character_slug: Annotated[
        str | None,
        Field(
            description='The character slug of a public Venice character. Discoverable as the "Public ID" on the published character page.'
        ),
    ] = None
    strip_thinking_response: Annotated[
        bool | None,
        Field(
            description="Strip <think></think> blocks from the response. Applicable only to reasoning / thinking models. Also available to use as a model feature suffix. Defaults to false.",
            examples=[False],
        ),
    ] = False
    disable_thinking: Annotated[
        bool | None,
        Field(
            description="On supported reasoning models, disables thinking and strips reasoning from the response. Direct OpenAI models with mandatory reasoning use their minimum supported effort when a thinking toggle is offered; reasoning tokens may still be generated and billed. Defaults to false.",
            examples=[False],
        ),
    ] = False
    enable_e2ee: Annotated[
        bool | None,
        Field(
            description="Enable end-to-end encryption for E2EE-capable models. When true (default), E2EE is used if E2EE headers are present. When false, the model runs in TEE-only mode even if E2EE headers are present. Only applicable to models with E2EE capability.",
            examples=[True],
        ),
    ] = True
    enable_web_search: Annotated[
        EnableWebSearch | None,
        Field(
            description="Enable web search for this request. Defaults to off. On will force web search on the request. Auto will enable it based on the model's discretion. Citations will be returned either in the first chunk of a streaming result, or in the non streaming response.",
            examples=["off"],
        ),
    ] = "off"
    enable_web_scraping: Annotated[
        bool | None,
        Field(
            description="Enable Venice web scraping of URLs in the latest user message using Firecrawl. Off by default.",
            examples=[False],
        ),
    ] = False
    enable_web_citations: Annotated[
        bool | None,
        Field(
            description="When web search is enabled, this will request that the LLM cite its sources using a ^index^ or ^i,j^ superscript format (e.g., ^1^). Defaults to false."
        ),
    ] = False
    include_search_results_in_stream: Annotated[
        bool | None,
        Field(
            description="Experimental feature - When set to true, the LLM will include search results in the stream as the first emitted chunk. Defaults to false."
        ),
    ] = False
    return_search_results_as_documents: Annotated[
        bool | None,
        Field(
            description='When set, search results are also surfaced in an OpenAI-compatible tool call named "venice_web_search_documents" to ease LangChain consumption.'
        ),
    ] = None
    include_venice_system_prompt: Annotated[
        bool | None,
        Field(
            description="Whether to include the Venice supplied system prompts along side specified system prompts. Defaults to true."
        ),
    ] = True
    enable_x_search: Annotated[
        bool | None,
        Field(
            description="Enable xAI native search (web + X/Twitter) for supported models. When enabled, the model performs web and X searches server-side instead of Venice search augmentation. Only available on models with supportsXSearch capability (e.g., grok-4-20). Additional per-search charges apply (~$0.01/search).",
            examples=[True],
        ),
    ] = False


class Type20(Enum):
    json_schema = "json_schema"


class ResponseFormat(VeniceBaseModel):
    json_schema: dict[str, Any]
    type: Type20


class Type21(Enum):
    json_object = "json_object"


class ResponseFormat1(VeniceBaseModel):
    type: Type21


class Type22(Enum):
    text = "text"


class ResponseFormat2(VeniceBaseModel):
    type: Type22


class Function(VeniceBaseModel):
    name: str


class ToolChoice(VeniceBaseModel):
    function: Function
    type: str


class Type23(Enum):
    web_search = "web_search"
    x_search = "x_search"


class Tools(VeniceBaseModel):
    type: Type23


class Function1(VeniceBaseModel):
    description: str | None = None
    name: str
    parameters: dict[str, Any] | None = None
    strict: Annotated[
        bool | None,
        Field(
            description="If set to true, the model will follow the exact schema defined in the parameters field. Only a subset of JSON Schema is supported when strict is true.",
            examples=[False],
        ),
    ] = False


class Tools1(VeniceBaseModel):
    function: Function1
    id: str | None = None
    type: str | None = None


class ChatCompletionRequest(VeniceBaseModel):
    frequency_penalty: Annotated[
        float | None,
        Field(
            description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.",
            ge=-2.0,
            le=2.0,
        ),
    ] = 0
    logprobs: Annotated[
        bool | None,
        Field(
            description="Whether to include log probabilities in the response. This is not supported by all models.",
            examples=[True],
        ),
    ] = None
    top_logprobs: Annotated[
        int | None,
        Field(
            description="The number of highest probability tokens to return for each token position.",
            examples=[1],
            ge=0,
        ),
    ] = None
    max_completion_tokens: Annotated[
        int | None,
        Field(
            description="An upper bound for the number of tokens that can be generated for a completion, including visible output tokens and reasoning tokens."
        ),
    ] = None
    max_temp: Annotated[
        float | None,
        Field(
            description="Maximum temperature value for dynamic temperature scaling.",
            examples=[1.5],
            ge=0.0,
            le=2.0,
        ),
    ] = None
    max_tokens: Annotated[
        int | None,
        Field(
            description="The maximum number of tokens that can be generated in the chat completion. This value can be used to control costs for text generated via API. Values of 0 or less are ignored and the model will use its default maximum. This value is now deprecated in favor of max_completion_tokens."
        ),
    ] = None
    messages: Annotated[
        list[Messages | Messages1 | Messages2 | Messages3 | Messages4],
        Field(
            description="A list of messages comprising the conversation so far. Depending on the model you use, different message types (modalities) are supported, like text and images. Non-multimodal models reject image content. For vision models that support multiple images (supportsMultipleImages), images are preserved across all messages in the conversation history. For single-image vision models, only the last image-containing message retains its images.",
            min_length=1,
        ),
    ]
    min_p: Annotated[
        float | None,
        Field(
            description="Sets a minimum probability threshold for token selection. Tokens with probabilities below this value are filtered out.",
            examples=[0.05],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    min_temp: Annotated[
        float | None,
        Field(
            description="Minimum temperature value for dynamic temperature scaling.",
            examples=[0.1],
            ge=0.0,
            le=2.0,
        ),
    ] = None
    model: Annotated[
        str,
        Field(
            description='The ID of the model you wish to prompt. May also be a model trait, or a model compatibility mapping. See the models endpoint for a list of models available to you. You can use feature suffixes to enable features from the venice_parameters object. Please see "Model Feature Suffix" documentation for more details.',
            examples=["zai-org-glm-5-1"],
        ),
    ]
    n: Annotated[
        int | None,
        Field(
            description="How many chat completion choices to generate for each input message. Note that you will be charged based on the number of generated tokens across all of the choices. Keep n as 1 to minimize costs."
        ),
    ] = 1
    presence_penalty: Annotated[
        float | None,
        Field(
            description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.",
            ge=-2.0,
            le=2.0,
        ),
    ] = 0
    prompt_cache_key: Annotated[
        str | None,
        Field(
            description="When supplied, this field may be used to optimize conversation routing to improve cache performance and thus reduce latency.",
            examples=["random-string"],
        ),
    ] = None
    prompt_cache_retention: Annotated[
        PromptCacheRetention | None,
        Field(
            description='OpenAI-compatible parameter to control prompt cache retention. "extended" or "24h" extends retention to 24 hours for supported models.',
            examples=["24h"],
        ),
    ] = None
    repetition_penalty: Annotated[
        float | None,
        Field(
            description="The parameter for repetition penalty. 1.0 means no penalty. Values > 1.0 discourage repetition.",
            examples=[1.2],
            ge=0.0,
        ),
    ] = None
    reasoning: Annotated[
        Reasoning | None,
        Field(description="Configuration for reasoning behavior on supported models."),
    ] = None
    reasoning_effort: Annotated[
        ReasoningEffort | None,
        Field(
            description="OpenAI-compatible parameter to control reasoning effort level for supported models. Takes precedence over reasoning.effort if both are provided. Direct OpenAI models validate concrete levels against their reasoningEffortOptions; none and minimal may map to the minimum supported effort on mandatory-reasoning models, with reasoning tokens still billed.",
            examples=["medium"],
        ),
    ] = None
    seed: Annotated[
        int | None,
        Field(
            description="The random seed used to generate the response. This is useful for reproducibility.",
            examples=[42],
            gt=0,
        ),
    ] = None
    stop: Annotated[
        str | Stop | Any | None,
        Field(
            description="Up to 4 sequences where the API will stop generating further tokens. Defaults to null."
        ),
    ] = None
    stop_token_ids: Annotated[
        list[float] | None,
        Field(
            description="Array of token IDs where the API will stop generating further tokens.",
            examples=[[151643, 151645]],
        ),
    ] = None
    stream: Annotated[
        bool | None,
        Field(
            description="Whether to stream back partial progress. Defaults to false.",
            examples=[True],
        ),
    ] = None
    stream_options: StreamOptions | None = None
    temperature: Annotated[
        float | None,
        Field(
            description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. We generally recommend altering this or top_p but not both.",
            examples=[0.7],
            ge=0.0,
            le=2.0,
        ),
    ] = None
    top_k: Annotated[
        int | None,
        Field(
            description="The number of highest probability vocabulary tokens to keep for top-k-filtering.",
            examples=[40],
            ge=0,
        ),
    ] = None
    top_p: Annotated[
        float | None,
        Field(
            description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.",
            examples=[0.9],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    user: Annotated[
        str | None,
        Field(
            description="This field is discarded on the request but is supported in the Venice API for compatibility with OpenAI clients. It is not an alias of anon_user_id."
        ),
    ] = None
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    fallbacks: Annotated[
        list[Fallback] | None,
        Field(
            description="Anthropic beta parameter for Claude Fable 5 server-side refusal fallback. Forwarded only for direct Anthropic routes; ignored for other providers.",
            examples=[[{"model": "claude-opus-4-8"}]],
            max_length=10,
        ),
    ] = None
    store: Annotated[
        bool | None,
        Field(
            description="This field is accepted for OpenAI compatibility but is not used by Venice."
        ),
    ] = None
    verbosity: Annotated[
        Verbosity | None,
        Field(
            description="Controls the verbosity of the text response. Currently supported values are `low`, `medium`, and `high`.",
            examples=["low"],
        ),
    ] = None
    text: Annotated[
        Text | None,
        Field(description="OpenAI-compatible text configuration parameter."),
    ] = None
    include: Annotated[
        list[str] | None,
        Field(
            description="OpenAI-compatible parameter specifying additional data to include in the response."
        ),
    ] = None
    metadata: Annotated[
        dict[str, str] | None,
        Field(description="OpenAI-compatible metadata parameter for request tracking."),
    ] = None
    venice_parameters: Annotated[
        VeniceParameters | None,
        Field(
            description="Unique parameters to Venice's API implementation. Customize these to control the behavior of the model."
        ),
    ] = None
    parallel_tool_calls: Annotated[
        bool | None,
        Field(
            description="Whether to enable parallel function calling during tool use.",
            examples=[False],
        ),
    ] = True
    response_format: Annotated[
        ResponseFormat | ResponseFormat1 | ResponseFormat2 | None,
        Field(description="Format in which the response should be returned."),
    ] = None
    tool_choice: ToolChoice | str | None = None
    tools: Annotated[
        list[Tools | Tools1] | None,
        Field(
            description="A list of tools the model may call. Currently, only functions are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for."
        ),
    ] = None


class Type24(Enum):
    ephemeral = "ephemeral"


class CacheControl10(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type24,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class InputAudio1(VeniceBaseModel):
    data: Annotated[
        str,
        Field(
            description="Base64-encoded audio data. Direct URLs are not supported for audio content."
        ),
    ]
    format: Annotated[
        Format | None,
        Field(
            description="The format of the audio file. Common formats include wav, mp3, aac, ogg, flac, m4a. Defaults to wav.",
            examples=["wav"],
        ),
    ] = "wav"


class Type25(Enum):
    input_audio = "input_audio"


class ChatCompletionContentPartInputAudio(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl10 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    input_audio: Annotated[
        InputAudio1,
        Field(
            description="Object containing the base64-encoded audio data and format",
            title="Input Audio Object",
        ),
    ]
    type: Type25


class Type26(Enum):
    ephemeral = "ephemeral"


class CacheControl11(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type26,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type27(Enum):
    video_url = "video_url"


class ChatCompletionContentPartVideoUrl(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl11 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    type: Type27
    video_url: Annotated[
        VideoUrl,
        Field(
            description="Object containing the video URL information",
            title="Video URL Object",
        ),
    ]


class Type28(Enum):
    web_search_call = "web_search_call"


class Status(Enum):
    in_progress = "in_progress"
    searching = "searching"
    completed = "completed"
    failed = "failed"
    incomplete = "incomplete"


class Type29(Enum):
    search = "search"


class Type30(Enum):
    url = "url"


class Source(VeniceBaseModel):
    type: Type30
    url: str


class Action(VeniceBaseModel):
    type: Type29
    query: str | None = None
    queries: list[str] | None = None
    sources: list[Source] | None = None


class Type31(Enum):
    open_page = "open_page"


class Action1(VeniceBaseModel):
    type: Type31
    url: str | None = None


class Type32(Enum):
    find_in_page = "find_in_page"


class Action2(VeniceBaseModel):
    type: Type32
    url: str
    pattern: str


class Input(VeniceBaseModel):
    type: Type28
    id: str
    status: Status
    action: Action | Action1 | Action2 | None = None


class Type33(Enum):
    message = "message"


class Role5(Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    developer = "developer"


class Type34(Enum):
    input_text = "input_text"


class Content5(VeniceBaseModel):
    type: Type34
    text: str


class Type35(Enum):
    input_image = "input_image"


class ImageUrl1(VeniceBaseModel):
    url: str
    detail: Detail | None = None


class Content6(VeniceBaseModel):
    type: Type35
    image_url: str | ImageUrl1
    detail: Detail | None = None


class Type36(Enum):
    output_text = "output_text"


class Content7(VeniceBaseModel):
    type: Type36
    text: str
    annotations: list[Any] | None = None


class Status1(Enum):
    completed = "completed"
    in_progress = "in_progress"
    incomplete = "incomplete"


class Input1(VeniceBaseModel):
    type: Type33
    role: Role5
    content: str | list[Content5 | Content6 | Content7]
    id: str | None = None
    status: Status1 | None = None


class Type37(Enum):
    input_text = "input_text"


class Content8(VeniceBaseModel):
    type: Type37
    text: str


class Type38(Enum):
    input_image = "input_image"


class ImageUrl2(VeniceBaseModel):
    url: str
    detail: Detail | None = None


class Content9(VeniceBaseModel):
    type: Type38
    image_url: str | ImageUrl2
    detail: Detail | None = None


class Type39(Enum):
    output_text = "output_text"


class Content10(VeniceBaseModel):
    type: Type39
    text: str
    annotations: list[Any] | None = None


class Type40(Enum):
    text = "text"


class Content11(VeniceBaseModel):
    type: Type40
    text: str


class Type41(Enum):
    image_url = "image_url"


class ImageUrl3(VeniceBaseModel):
    url: str
    detail: Detail | None = None


class Content12(VeniceBaseModel):
    type: Type41
    image_url: str | ImageUrl3


class Input2(VeniceBaseModel):
    role: Role5
    content: str | list[Content8 | Content9 | Content10 | Content11 | Content12]
    id: str | None = None
    status: Status1 | None = None


class Type42(Enum):
    reasoning = "reasoning"


class Type43(Enum):
    summary_text = "summary_text"


class Summary1(VeniceBaseModel):
    type: Type43
    text: str


class Status3(Enum):
    completed = "completed"
    in_progress = "in_progress"


class Input3(VeniceBaseModel):
    type: Type42
    id: str | None = None
    summary: list[str | Summary1] | None = None
    content: str | list[Any] | Any | None = None
    encrypted_content: str | None = None
    status: Status3 | None = None


class Type44(Enum):
    function_call = "function_call"


class Status4(Enum):
    completed = "completed"
    in_progress = "in_progress"
    incomplete = "incomplete"


class Input4(VeniceBaseModel):
    type: Type44
    id: str | None = None
    call_id: str
    name: str
    namespace: str | None = None
    arguments: str
    status: Status4 | None = None


class Type45(Enum):
    function_call_output = "function_call_output"


class Input5(VeniceBaseModel):
    type: Type45
    call_id: str
    output: str | list[Any] | dict[str, Any] | float | bool | Any


class Type46(Enum):
    item_reference = "item_reference"


class Input6(VeniceBaseModel):
    type: Type46
    id: str


class Type47(Enum):
    custom_tool_call = "custom_tool_call"


class Input7(VeniceBaseModel):
    type: Type47
    id: str | None = None
    call_id: str
    name: str
    namespace: str | None = None
    input: str
    status: Status4 | None = None


class Type48(Enum):
    custom_tool_call_output = "custom_tool_call_output"


class Input8(VeniceBaseModel):
    type: Type48
    call_id: str
    output: str | list[Any] | dict[str, Any] | float | bool | Any


class Type49(Enum):
    additional_tools = "additional_tools"


class Role7(Enum):
    developer = "developer"


class Type50(Enum):
    function = "function"


class Function2(VeniceBaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    strict: bool | None = None
    defer_loading: bool | None = None


class Tools2(VeniceBaseModel):
    type: Type50
    defer_loading: bool | None = None
    function: Function2


class Type51(Enum):
    tool_search = "tool_search"


class Execution(Enum):
    client = "client"


class Type52(Enum):
    object = "object"


class Parameters(VeniceBaseModel):
    type: Type52


class Tools3(VeniceBaseModel):
    type: Type51
    execution: Execution
    description: str | None = None
    parameters: Parameters


class Type53(Enum):
    web_search = "web_search"


class SearchContextSize(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Type54(Enum):
    approximate = "approximate"


class UserLocation(VeniceBaseModel):
    type: Type54 | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    timezone: str | None = None


class Tools4(VeniceBaseModel):
    type: Type53
    search_context_size: SearchContextSize | None = None
    user_location: UserLocation | None = None
    external_web_access: Annotated[
        bool | None,
        Field(
            description="Set to `false` to declare the tool without live web access. This declaration does not enable Venice web search."
        ),
    ] = None


class Type55(Enum):
    x_search = "x_search"


class Tools5(VeniceBaseModel):
    type: Type55
    allowed_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    excluded_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    from_date: str | None = None
    to_date: str | None = None
    enable_image_understanding: bool | None = None
    enable_video_understanding: bool | None = None


class Type56(Enum):
    code_interpreter = "code_interpreter"


class Container(VeniceBaseModel):
    image: str | None = None


class Tools6(VeniceBaseModel):
    type: Type56
    container: Container | None = None


class Type57(Enum):
    file_search = "file_search"


class RankingOptions(VeniceBaseModel):
    ranker: str | None = None
    score_threshold: float | None = None


class Tools7(VeniceBaseModel):
    type: Type57
    vector_store_ids: list[str] | None = None
    max_num_results: int | None = None
    ranking_options: RankingOptions | None = None


class Type58(Enum):
    computer_use_preview = "computer_use_preview"


class Tools8(VeniceBaseModel):
    type: Type58
    display_width: int | None = None
    display_height: int | None = None
    environment: str | None = None


class Tools9(VeniceBaseModel):
    type: str


class Input9(VeniceBaseModel):
    type: Type49
    role: Role7 | None = None
    tools: list[Tools2 | Tools3 | Tools4 | Tools5 | Tools6 | Tools7 | Tools8 | Tools9]
    id: str | None = None


class Type59(Enum):
    tool_search_call = "tool_search_call"


class Input10(VeniceBaseModel):
    type: Type59
    id: str | None = None
    call_id: Annotated[str, Field(min_length=1)]
    execution: Execution
    arguments: dict[str, Any]
    status: Status4 | None = None


class Type60(Enum):
    tool_search_output = "tool_search_output"


class Status7(Enum):
    completed = "completed"


class Type61(Enum):
    function = "function"


class Tools10(VeniceBaseModel):
    type: Type61
    defer_loading: bool | None = None
    function: Function2


class Type62(Enum):
    tool_search = "tool_search"


class Type63(Enum):
    object = "object"


class Parameters1(VeniceBaseModel):
    type: Type63


class Tools11(VeniceBaseModel):
    type: Type62
    execution: Execution
    description: str | None = None
    parameters: Parameters1


class Type64(Enum):
    web_search = "web_search"


class Type65(Enum):
    approximate = "approximate"


class UserLocation1(VeniceBaseModel):
    type: Type65 | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    timezone: str | None = None


class Tools12(VeniceBaseModel):
    type: Type64
    search_context_size: SearchContextSize | None = None
    user_location: UserLocation1 | None = None
    external_web_access: Annotated[
        bool | None,
        Field(
            description="Set to `false` to declare the tool without live web access. This declaration does not enable Venice web search."
        ),
    ] = None


class Type66(Enum):
    x_search = "x_search"


class Tools13(VeniceBaseModel):
    type: Type66
    allowed_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    excluded_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    from_date: str | None = None
    to_date: str | None = None
    enable_image_understanding: bool | None = None
    enable_video_understanding: bool | None = None


class Type67(Enum):
    code_interpreter = "code_interpreter"


class Tools14(VeniceBaseModel):
    type: Type67
    container: Container | None = None


class Type68(Enum):
    file_search = "file_search"


class Tools15(VeniceBaseModel):
    type: Type68
    vector_store_ids: list[str] | None = None
    max_num_results: int | None = None
    ranking_options: RankingOptions | None = None


class Type69(Enum):
    computer_use_preview = "computer_use_preview"


class Tools16(VeniceBaseModel):
    type: Type69
    display_width: int | None = None
    display_height: int | None = None
    environment: str | None = None


class Tools17(VeniceBaseModel):
    type: str


class Input11(VeniceBaseModel):
    type: Type60
    id: str | None = None
    call_id: Annotated[str, Field(min_length=1)]
    execution: Execution
    status: Status7 | None = None
    tools: list[Tools10 | Tools11 | Tools12 | Tools13 | Tools14 | Tools15 | Tools16 | Tools17]


class Summary2(Enum):
    auto = "auto"
    concise = "concise"
    detailed = "detailed"


class Reasoning1(VeniceBaseModel):
    effort: Annotated[
        Effort | None,
        Field(description="Controls reasoning effort level for supported models."),
    ] = None
    enabled: Annotated[
        bool | None,
        Field(
            description="Set to false to disable reasoning on supported models. Ignored when an effort level is provided."
        ),
    ] = None
    summary: Annotated[Summary2 | None, Field(description="Controls reasoning summary format.")] = (
        None
    )


class Type70(Enum):
    function = "function"


class Tools18(VeniceBaseModel):
    type: Type70
    defer_loading: bool | None = None
    function: Function2


class Type71(Enum):
    tool_search = "tool_search"


class Type72(Enum):
    object = "object"


class Parameters2(VeniceBaseModel):
    type: Type72


class Tools19(VeniceBaseModel):
    type: Type71
    execution: Execution
    description: str | None = None
    parameters: Parameters2


class Type73(Enum):
    web_search = "web_search"


class Type74(Enum):
    approximate = "approximate"


class UserLocation2(VeniceBaseModel):
    type: Type74 | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    timezone: str | None = None


class Tools20(VeniceBaseModel):
    type: Type73
    search_context_size: SearchContextSize | None = None
    user_location: UserLocation2 | None = None
    external_web_access: Annotated[
        bool | None,
        Field(
            description="Set to `false` to declare the tool without live web access. This declaration does not enable Venice web search."
        ),
    ] = None


class Type75(Enum):
    x_search = "x_search"


class Tools21(VeniceBaseModel):
    type: Type75
    allowed_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    excluded_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    from_date: str | None = None
    to_date: str | None = None
    enable_image_understanding: bool | None = None
    enable_video_understanding: bool | None = None


class Type76(Enum):
    code_interpreter = "code_interpreter"


class Tools22(VeniceBaseModel):
    type: Type76
    container: Container | None = None


class Type77(Enum):
    file_search = "file_search"


class Tools23(VeniceBaseModel):
    type: Type77
    vector_store_ids: list[str] | None = None
    max_num_results: int | None = None
    ranking_options: RankingOptions | None = None


class Type78(Enum):
    computer_use_preview = "computer_use_preview"


class Tools24(VeniceBaseModel):
    type: Type78
    display_width: int | None = None
    display_height: int | None = None
    environment: str | None = None


class Tools25(VeniceBaseModel):
    type: str


class ToolChoice1(Enum):
    auto = "auto"


class ToolChoice2(Enum):
    none = "none"


class ToolChoice3(Enum):
    required = "required"


class Type79(Enum):
    function = "function"
    custom = "custom"


class ToolChoice4(VeniceBaseModel):
    type: Type79
    name: str
    namespace: str | None = None


class Type80(Enum):
    function = "function"


class Function5(VeniceBaseModel):
    name: str


class ToolChoice5(VeniceBaseModel):
    type: Type80
    function: Function5


class PromptCacheRetention1(Enum):
    in_memory = "in_memory"
    field_24h = "24h"
    default = "default"
    extended = "extended"


class Type81(Enum):
    text = "text"


class Format2(VeniceBaseModel):
    type: Type81


class Type82(Enum):
    json_object = "json_object"


class Format3(VeniceBaseModel):
    type: Type82


class Type83(Enum):
    json_schema = "json_schema"


class Format4(VeniceBaseModel):
    type: Type83
    name: Annotated[str, Field(description="Name of the response format.", min_length=1)]
    schema_: Annotated[
        dict[str, Any],
        Field(alias="schema", description="JSON Schema the response must follow."),
    ]
    strict: Annotated[bool | None, Field(description="Whether to enforce the schema strictly.")] = (
        None
    )
    description: str | None = None


class Text1(VeniceBaseModel):
    format: Format2 | Format3 | Format4 | None = None


class VeniceParameters1(VeniceBaseModel):
    character_slug: Annotated[
        str | None,
        Field(description="The character slug of a public Venice character."),
    ] = None
    enable_e2ee: Annotated[
        bool | None,
        Field(
            description="Enable end-to-end encryption for E2EE-capable models. When true (default), E2EE is used if headers are present. When false, TEE-only mode is used."
        ),
    ] = None
    enable_web_search: Annotated[
        EnableWebSearch | None, Field(description="Enable web search for this request.")
    ] = "off"
    enable_web_scraping: Annotated[
        bool | None,
        Field(description="Enable Venice web scraping of URLs in the latest user message."),
    ] = None
    enable_web_citations: Annotated[
        bool | None, Field(description="Request that the LLM cite its sources.")
    ] = None
    include_venice_system_prompt: Annotated[
        bool | None,
        Field(description="Whether to include the Venice supplied system prompts."),
    ] = None
    include_search_results_in_stream: Annotated[
        bool | None,
        Field(description="Include search results in the stream as the first emitted chunk."),
    ] = None


class ResponsesRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The ID of the model to use. E2EE-capable models are not supported on /api/v1/responses; use /api/v1/chat/completions with the required E2EE headers instead.",
            examples=["zai-org-glm-5-1"],
        ),
    ]
    input: Annotated[
        str
        | list[
            Input
            | Input1
            | Input2
            | Input3
            | Input4
            | Input5
            | Input6
            | Input7
            | Input8
            | Input9
            | Input10
            | Input11
        ],
        Field(
            description="The input to generate a response for. Can be a simple string or an array of messages."
        ),
    ]
    instructions: Annotated[
        str | None,
        Field(description="System instructions for the model, applied before `input`."),
    ] = None
    include: Annotated[
        list[str] | None,
        Field(description="Additional response fields to include (OpenAI-compatible)."),
    ] = None
    max_output_tokens: Annotated[
        int | None, Field(description="Maximum number of tokens to generate.", gt=0)
    ] = None
    temperature: Annotated[
        float | None,
        Field(description="Sampling temperature between 0 and 2.", ge=0.0, le=2.0),
    ] = None
    top_p: Annotated[
        float | None, Field(description="Nucleus sampling parameter.", ge=0.0, le=1.0)
    ] = None
    fallbacks: Annotated[
        list[Fallback] | None,
        Field(
            description="Anthropic beta parameter for Claude Fable 5 server-side refusal fallback. Forwarded only for direct Anthropic routes; ignored for other providers.",
            examples=[[{"model": "claude-opus-4-8"}]],
            max_length=10,
        ),
    ] = None
    reasoning: Annotated[
        Reasoning1 | None,
        Field(
            description="Reasoning controls for models that support reasoning.",
            title="Reasoning Configuration",
        ),
    ] = None
    parallel_tool_calls: Annotated[
        bool | None,
        Field(description="Whether the model may call more than one tool in a single turn."),
    ] = None
    tools: Annotated[
        list[Tools18 | Tools19 | Tools20 | Tools21 | Tools22 | Tools23 | Tools24 | Tools25] | None,
        Field(description="A list of tools the model may call."),
    ] = None
    tool_choice: Annotated[
        ToolChoice1 | ToolChoice2 | ToolChoice3 | ToolChoice4 | ToolChoice5 | None,
        Field(description="Controls which tool is called by the model."),
    ] = None
    prompt_cache_retention: Annotated[
        PromptCacheRetention1 | None,
        Field(
            description='Prompt cache retention for supported OpenAI models. "24h" or "extended" keeps cached prefixes for up to 24 hours.',
            examples=["24h"],
        ),
    ] = None
    web_search: Annotated[bool | None, Field(description="Enable web search for this request.")] = (
        None
    )
    stream: Annotated[
        bool | None, Field(description="Whether to stream back partial progress.")
    ] = None
    text: Annotated[
        Text1 | None,
        Field(
            description="Text output options. `format` requests structured output: `json_schema` with a `name` and `schema`, or `json_object`. Models without structured output support return 400."
        ),
    ] = None
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    venice_parameters: Annotated[
        VeniceParameters1 | None,
        Field(
            description="Venice-specific options, such as web search, characters, and the Venice system prompt.",
            title="Venice Parameters",
        ),
    ] = None


class Object(Enum):
    response = "response"


class Status8(Enum):
    completed = "completed"
    failed = "failed"
    in_progress = "in_progress"
    cancelled = "cancelled"
    incomplete = "incomplete"


class Reason1(Enum):
    max_output_tokens = "max_output_tokens"
    content_filter = "content_filter"


class IncompleteDetails(VeniceBaseModel):
    reason: Reason1


class Type84(Enum):
    reasoning = "reasoning"


class Output(VeniceBaseModel):
    type: Type84
    id: str
    summary: list[str] | None = None
    encrypted_content: str | None = None


class Type85(Enum):
    message = "message"


class Status9(Enum):
    completed = "completed"
    in_progress = "in_progress"
    failed = "failed"
    incomplete = "incomplete"


class Role8(Enum):
    assistant = "assistant"


class Type86(Enum):
    output_text = "output_text"


class Type87(Enum):
    url_citation = "url_citation"


class Annotation(VeniceBaseModel):
    type: Type87
    url: str
    title: str | None = None
    start_index: int
    end_index: int


class ContentItem3(VeniceBaseModel):
    type: Type86
    text: str
    annotations: list[Annotation] | None = None


class Output1(VeniceBaseModel):
    type: Type85
    id: str
    status: Status9
    role: Role8
    content: list[ContentItem3]


class Type88(Enum):
    function_call = "function_call"


class Status10(Enum):
    completed = "completed"
    in_progress = "in_progress"
    incomplete = "incomplete"


class Output2(VeniceBaseModel):
    type: Type88
    id: str
    call_id: str
    name: str
    namespace: str | None = None
    arguments: str
    status: Status10


class Type89(Enum):
    custom_tool_call = "custom_tool_call"


class Output3(VeniceBaseModel):
    type: Type89
    id: str
    call_id: str
    name: str
    namespace: str | None = None
    input: str
    status: Status10


class Type90(Enum):
    tool_search_call = "tool_search_call"


class Output4(VeniceBaseModel):
    type: Type90
    id: str
    call_id: Annotated[str, Field(min_length=1)]
    execution: Execution
    arguments: dict[str, Any]
    status: Status10


class Type91(Enum):
    web_search_call = "web_search_call"


class Status13(Enum):
    completed = "completed"


class Type92(Enum):
    search = "search"


class Type93(Enum):
    url = "url"


class Source1(VeniceBaseModel):
    type: Type93
    url: str


class Action3(VeniceBaseModel):
    type: Type92
    query: str | None = None
    queries: list[str] | None = None
    sources: list[Source1] | None = None


class Type94(Enum):
    open_page = "open_page"


class Action4(VeniceBaseModel):
    type: Type94
    url: str | None = None


class Type95(Enum):
    find_in_page = "find_in_page"


class Action5(VeniceBaseModel):
    type: Type95
    url: str
    pattern: str


class Output5(VeniceBaseModel):
    type: Type91
    id: str
    status: Status13
    action: Action3 | Action4 | Action5 | None = None


class InputTokensDetails(VeniceBaseModel):
    cached_tokens: int | None = None


class OutputTokensDetails(VeniceBaseModel):
    reasoning_tokens: int | None = None


class Usage(VeniceBaseModel):
    input_tokens: int
    input_tokens_details: InputTokensDetails | None = None
    output_tokens: int
    output_tokens_details: OutputTokensDetails | None = None
    total_tokens: int


class Error3(VeniceBaseModel):
    code: str
    message: str


class ResponsesResponse(VeniceBaseModel):
    id: Annotated[
        str,
        Field(description="Unique identifier for the response.", examples=["resp_abc123"]),
    ]
    object: Annotated[Object, Field(description="The object type.")]
    created_at: Annotated[
        int, Field(description="Unix timestamp of when the response was created.")
    ]
    model: Annotated[str, Field(description="The model used for the response.")]
    status: Annotated[Status8, Field(description="The status of the response.")]
    incomplete_details: Annotated[
        IncompleteDetails | None,
        Field(
            description="Why generation ended before completion; partial output and usage are retained."
        ),
    ] = None
    output: Annotated[
        list[Output | Output1 | Output2 | Output3 | Output4 | Output5],
        Field(description="The output items generated by the model."),
    ]
    usage: Annotated[Usage | None, Field(description="Token usage statistics.", title="Usage")] = (
        None
    )
    error: Annotated[
        Error3 | None,
        Field(description="Error information if the response failed.", title="Error"),
    ] = None


class Format5(Enum):
    jpeg = "jpeg"
    png = "png"
    webp = "webp"


class Quality(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class StyleReference(VeniceBaseModel):
    image: Annotated[
        str | AnyUrl,
        Field(
            description="A style reference image as a base64-encoded string (raw or data URI) or a URL starting with http:// or https://. Must be less than 8MB.",
            examples=["https://example.com/style-reference.png"],
        ),
    ]
    strength: Annotated[
        float | None,
        Field(
            description="How strongly the reference guides the output (0.1–1). Defaults to 0.5. Ignored by models where supportsStyleReferenceStrength is false.",
            examples=[0.5],
            ge=0.1,
            le=1.0,
        ),
    ] = None


class GenerateImageRequest(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    cfg_scale: Annotated[
        float | None,
        Field(
            description="CFG scale parameter. Higher values lead to more adherence to the prompt.",
            examples=[7.5],
            gt=0.0,
            le=20.0,
        ),
    ] = None
    embed_exif_metadata: Annotated[
        bool | None,
        Field(
            description="Embed prompt generation information into the image's EXIF metadata.",
            examples=[False],
        ),
    ] = False
    format: Annotated[
        Format5 | None,
        Field(
            description="The image format to return. WebP are smaller and optimized for web use. PNG are higher quality but larger in file size. ",
            examples=["webp"],
        ),
    ] = "webp"
    height: Annotated[
        int | None,
        Field(description="Height of the generated image.", examples=[1024], gt=0, le=1280),
    ] = 1024
    hide_watermark: Annotated[
        bool | None,
        Field(
            description="Whether to hide the Venice watermark. Venice may ignore this parameter for certain generated content.",
            examples=[False],
        ),
    ] = False
    inpaint: Annotated[
        Any | None,
        Field(
            deprecated=True,
            description="This feature is deprecated and was disabled on May 19th, 2025. A revised in-painting API will be launched in the near future.",
        ),
    ] = None
    lora_strength: Annotated[
        int | None,
        Field(
            description="Lora strength for the model. Only applies if the model uses additional Loras.",
            examples=[50],
            ge=0,
            le=100,
        ),
    ] = None
    model: Annotated[
        str,
        Field(
            description="The model to use for image generation.",
            examples=["grok-imagine-image"],
        ),
    ]
    negative_prompt: Annotated[
        str | None,
        Field(
            description="A description of what should not be in the image. Character limit is model specific and is listed in the promptCharacterLimit constraint in the model list endpoint.",
            examples=["Clouds, Rain, Snow"],
            max_length=7500,
        ),
    ] = None
    prompt: Annotated[
        str,
        Field(
            description="The description for the image. Character limit is model specific and is listed in the promptCharacterLimit setting in the model list endpoint.",
            examples=["A beautiful sunset over a mountain range"],
            max_length=7500,
            min_length=1,
        ),
    ]
    return_binary: Annotated[
        bool | None,
        Field(
            description="Whether to return binary image data instead of base64.",
            examples=[False],
        ),
    ] = False
    variants: Annotated[
        int | None,
        Field(
            description="Number of images to generate (1–4). Only supported when return_binary is false. Variants the model provider explicitly rejects under its content policy are omitted from a successful partial response. Other moderation outcomes can still return blacked-out images; check `x-venice-is-content-violation`.",
            examples=[3],
            ge=1,
            le=4,
        ),
    ] = None
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to blur images classified as adult content. Defaults to true. Set to false to receive unblurred output. No Pro subscription is required, and the mature filter setting in the Venice app does not affect this. The x-venice-is-blurred response header reports whether the returned image was blurred.",
            examples=[False],
        ),
    ] = True
    seed: Annotated[
        int | None,
        Field(
            description="Random seed for generation. If not provided, a random seed will be used.",
            examples=[123456789],
            ge=-999999999,
            le=999999999,
        ),
    ] = 0
    steps: Annotated[
        int | None,
        Field(
            description="Number of inference steps. This model does not support steps - this field is ignored.",
            examples=[8],
        ),
    ] = 8
    style_preset: Annotated[
        str | None,
        Field(
            description="An image style to apply to the image. Visit https://docs.venice.ai/api-reference/endpoint/image/styles for more details.",
            examples=["3D Model"],
        ),
    ] = None
    aspect_ratio: Annotated[
        str | None,
        Field(
            description='Aspect ratio (utilized by certain image models including Nano Banana). Examples: "1:1", "16:9".',
            examples=[61],
        ),
    ] = None
    resolution: Annotated[
        str | None,
        Field(
            description='Resolution (utilized by certain image models including Nano Banana). Examples: "1K", "2K", "4K".',
            examples=["1K"],
        ),
    ] = None
    quality: Annotated[
        Quality | None,
        Field(
            description="Output quality for supported models (e.g. GPT Image 2 / GPT Image 2 Edit). Higher values can increase the final request charge. See the model list for supported options.",
            examples=["high"],
        ),
    ] = None
    transparent_background: Annotated[
        bool | None,
        Field(
            description="Return the image with a transparent background (alpha channel). Only supported by models with `supportsTransparentBackground: true` in their constraints (see GET /api/v1/models), and requires `format` png or webp; otherwise the request is rejected. Omit or set to false to keep the model default background.",
            examples=[False],
        ),
    ] = None
    enable_web_search: Annotated[
        bool | None,
        Field(
            description="Enable web search for the image generation task. This will allow the model to use the latest information from the web to generate the image. Only supported by certain models. If web search is used, additional credits are getting charged.",
            examples=[False],
        ),
    ] = None
    disable_prompt_optimization_thinking: Annotated[
        bool | None,
        Field(
            description="Skip the model's prompt-optimization thinking step for faster generation. Only supported by models with `supportsOptimizePromptThinking`; ignored by others. Omit to use the model default.",
            examples=[False],
        ),
    ] = None
    enhance_prompt: Annotated[
        bool | None,
        Field(
            description="Rewrite the prompt before generation to add clarifying visual detail. Additional credits are charged when a rewrite is generated. Adds up to ~30 seconds before generation starts. When enhancement is applied, the final prompt is returned URL-encoded in the `x-venice-enhanced-prompt` response header. Defaults to false.",
            examples=[False],
        ),
    ] = None
    width: Annotated[
        int | None,
        Field(description="Width of the generated image.", examples=[1024], gt=0, le=1280),
    ] = 1024
    style_references: Annotated[
        list[StyleReference] | None,
        Field(
            description="Style reference images that guide the aesthetic of the generated image. Only supported by models with `supportsStyleReferences: true` (see GET /api/v1/models for the per-model `maxStyleReferences` limit).",
            examples=[[{"image": "https://example.com/style-reference.png", "strength": 0.5}]],
        ),
    ] = None


class Background(Enum):
    transparent = "transparent"
    opaque = "opaque"
    auto = "auto"


class Moderation(Enum):
    low = "low"
    auto = "auto"


class OutputFormat(Enum):
    jpeg = "jpeg"
    png = "png"
    webp = "webp"


class Quality1(Enum):
    auto = "auto"
    high = "high"
    medium = "medium"
    low = "low"
    hd = "hd"
    standard = "standard"


class ResponseFormat3(Enum):
    b64_json = "b64_json"
    url = "url"


class Size(Enum):
    auto = "auto"
    field_256x256 = "256x256"
    field_512x512 = "512x512"
    field_1024x1024 = "1024x1024"
    field_1536x1024 = "1536x1024"
    field_1024x1536 = "1024x1536"
    field_1792x1024 = "1792x1024"
    field_1024x1792 = "1024x1792"


class Style(Enum):
    vivid = "vivid"
    natural = "natural"


class SimpleGenerateImageRequest(VeniceBaseModel):
    background: Annotated[
        Background | None,
        Field(
            description="Set to transparent to return the image with a transparent background (alpha channel). transparent is only supported by models with `supportsTransparentBackground: true` in their constraints (see GET /api/v1/models) and with output_format png or webp; otherwise the request is rejected. If the model does not exist, the default image model is used. auto, opaque and null keep the model default background.",
            examples=["auto"],
        ),
    ] = "auto"
    model: Annotated[
        str | None,
        Field(
            description="The model to use for image generation. Defaults to Venice's default image model. If a non-existent model is specified (ie an OpenAI model name), it will default to Venice's default image model.",
            examples=["grok-imagine-image"],
        ),
    ] = "default"
    moderation: Annotated[
        Moderation | None,
        Field(
            description="Controls blurring of images classified as adult content. auto (the default, also used when null) blurs them; low returns unblurred output. This is the OpenAI-compatible equivalent of safe_mode on /image/generate. No Pro subscription is required, and the mature filter setting in the Venice app does not affect this. The x-venice-is-blurred response header reports whether the returned image was blurred.",
            examples=["auto"],
        ),
    ] = "auto"
    n: Annotated[
        int | None,
        Field(
            description="Number of images to generate. Venice presently only supports 1 image per request.",
            examples=[1],
            ge=1,
            le=1,
        ),
    ] = 1
    output_compression: Annotated[
        int | None,
        Field(
            description="This parameter is not used in Venice image generation but is supported for compatibility with OpenAI API",
            ge=0,
            le=100,
        ),
    ] = 100
    output_format: Annotated[
        OutputFormat | None,
        Field(description="Output format for generated images", examples=["png"]),
    ] = "png"
    prompt: Annotated[
        str,
        Field(
            description="A text description of the desired image.",
            examples=["A beautiful sunset over mountain ranges"],
            max_length=1500,
            min_length=1,
        ),
    ]
    quality: Annotated[
        Quality1 | None,
        Field(
            description="This parameter is not used in Venice image generation but is supported for compatibility with OpenAI API",
            examples=["auto"],
        ),
    ] = "auto"
    response_format: Annotated[
        ResponseFormat3 | None,
        Field(
            description="Response format. URL will be a data URL.",
            examples=["b64_json"],
        ),
    ] = "b64_json"
    size: Annotated[
        Size | None,
        Field(
            description="Size of generated images. Default is 1024x1024",
            examples=["1024x1024"],
        ),
    ] = "auto"
    style: Annotated[
        Style | None,
        Field(
            description="This parameter is not used in Venice image generation but is supported for compatibility with OpenAI API",
            examples=["natural"],
        ),
    ] = "natural"
    user: Annotated[
        str | None,
        Field(
            description="This parameter is discarded and is supported for compatibility with OpenAI API. It is not an alias of anon_user_id.",
            examples=["user123"],
        ),
    ] = None
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None


class UpscaleImageRequest(VeniceBaseModel):
    creativity: Annotated[
        float | None,
        Field(
            description="How much detail and texture the upscaler adds. Higher values add more; lower values stay closer to the source. Clamped to the 0–0.02 range.",
            examples=[0.01],
        ),
    ] = 0.01
    image: Annotated[
        Any | str,
        Field(
            description="The image to upscale. Can be either a file upload or a base64-encoded string. Image dimensions must be at least 65536 pixels and final dimensions after scaling must not exceed 16777216 pixels. File size must be less than 25MB."
        ),
    ]
    scale: Annotated[
        float | None,
        Field(
            description="The scale factor for upscaling the image. Must be either 2 or 4. A scale of 4 with large images will result in the scale being dynamically reduced to ensure the final image stays within the maximum size limits.",
            examples=[2],
            ge=2.0,
            le=4.0,
        ),
    ] = 2


class AspectRatio(Enum):
    auto = "auto"
    field_61 = 61
    field_182 = 182
    field_969 = 969
    field_1269 = 1269
    field_556 = 556
    field_123 = 123
    field_184 = 184
    field_243 = 243
    field_245 = 245


class EditImageRequest(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    aspect_ratio: Annotated[
        AspectRatio | None,
        Field(
            description="The aspect ratio for the output image. Use 'auto' or omit this parameter to infer the closest supported aspect ratio from the input image when explicit sizing is required by the model. Supported values vary by model - check GET /api/v1/models for model-specific options.",
            examples=[969],
        ),
    ] = None
    disable_prompt_optimization_thinking: Annotated[
        bool | None,
        Field(
            description="Skip the model's prompt-optimization thinking step for faster generation. Only supported by models with `supportsOptimizePromptThinking`; ignored by others. Omit to use the model default.",
            examples=[False],
        ),
    ] = None
    enhance_prompt: Annotated[
        bool | None,
        Field(
            description="Rewrite the edit prompt using the input image before editing to add clarifying detail. Additional credits are charged when a rewrite is generated. Adds up to ~30 seconds. When enhancement is applied, the final prompt is returned URL-encoded in the `x-venice-enhanced-prompt` response header. Defaults to false.",
            examples=[False],
        ),
    ] = None
    resolution: Annotated[
        str | None,
        Field(
            description='Resolution tier for the output image (e.g. "1K", "2K", "4K"). Supported values vary by model - check GET /api/v1/models for model-specific options. Defaults to "1K" when not specified.',
            examples=["1K"],
            max_length=10,
            min_length=1,
        ),
    ] = None
    image: Annotated[
        Any | str | AnyUrl,
        Field(
            description="The image to edit. Can be either a file upload, a base64-encoded string, or a URL starting with http:// or https://. Image dimensions must be at least 65536 pixels and must not exceed 33177600 pixels. File size must be less than 25MB."
        ),
    ]
    model: Annotated[
        str | None,
        Field(description="The model ID to use for image editing.", min_length=1),
    ] = "firered-image-edit"
    modelId: Annotated[
        str | None,
        Field(
            deprecated=True,
            description='Deprecated: Use "model" instead. The model ID to use for image editing.',
            min_length=1,
        ),
    ] = None
    output_format: Annotated[
        OutputFormat | None,
        Field(
            description="Output format for the edited image. Accepts jpeg, jpg, png, or webp. When omitted, the format is inferred from resolution: PNG for 1K edits and JPEG for 2K/4K edits, or PNG at any resolution when transparent_background is true.",
            examples=["png"],
        ),
    ] = "png"
    prompt: Annotated[
        str,
        Field(
            description='The text directions to edit or modify the image. Short, descriptive prompts work best (e.g., "remove the tree", "change the sky to sunrise"). Character limit is model specific and is listed in the promptCharacterLimit setting in the model list endpoint.',
            examples=["Change the color of the sky to a sunrise"],
            max_length=32768,
            min_length=1,
        ),
    ]
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to blur images classified as adult content. Defaults to true. Set to false to receive unblurred output. No Pro subscription is required, and the mature filter setting in the Venice app does not affect this. The x-venice-is-blurred response header reports whether the returned image was blurred.",
            examples=[False],
        ),
    ] = True
    transparent_background: Annotated[
        bool | None,
        Field(
            description="Return the edited image with a transparent background (alpha channel). Only supported by models with `supportsTransparentBackground: true` in their constraints (see GET /api/v1/models), and requires `output_format` png or webp when set; otherwise the request is rejected. Omit or set to false to keep the model default background.",
            examples=[False],
        ),
    ] = None


class Quality2(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class MultiEditImageRequest(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    aspect_ratio: Annotated[
        AspectRatio | None,
        Field(
            description="The aspect ratio for the output image. Use 'auto' or omit this parameter to infer the closest supported aspect ratio from the first input image when explicit sizing is required by the model.",
            examples=[969],
        ),
    ] = None
    modelId: Annotated[
        str | None,
        Field(description="The model ID to use for multi-edit.", min_length=1),
    ] = "firered-image-edit"
    output_format: Annotated[
        OutputFormat | None,
        Field(
            description="Output format for the edited image. Accepts jpeg, jpg, png, or webp. When omitted, the format is inferred from resolution: PNG for 1K edits and JPEG for 2K/4K edits, or PNG at any resolution when transparent_background is true.",
            examples=["png"],
        ),
    ] = "png"
    prompt: Annotated[
        str,
        Field(
            description='The text directions to edit or modify the image. Short, descriptive prompts work best (e.g., "remove the tree", "change the sky to sunrise"). Character limit is model specific and is listed in the promptCharacterLimit setting in the model list endpoint.',
            max_length=32768,
            min_length=1,
        ),
    ]
    images: Annotated[
        list[AnyUrl | str],
        Field(
            description="Images used for multi-editing (minimum 1). The maximum is model-specific — see `capabilities.maxInputImages` from GET /api/v1/models. The first image is treated as the base image, and the remaining images are used as edit layers/masks. Each image can be a base64-encoded string or a URL starting with http:// or https://. Image dimensions must be at least 65536 pixels and must not exceed 33177600 pixels. File size must be less than 25MB."
        ),
    ]
    quality: Annotated[
        Quality2 | None,
        Field(
            description="Output quality for supported models (e.g. GPT Image 2 / GPT Image 2 Edit). Higher values can increase the final request charge. See the model list for supported options.",
            examples=["high"],
        ),
    ] = None
    resolution: Annotated[
        str | None,
        Field(
            description='Resolution tier for the output image (e.g. "1K", "2K", "4K"). Supported values vary by model - check GET /api/v1/models for model-specific options. Defaults to "1K" when not specified.',
            examples=["1K"],
            max_length=10,
            min_length=1,
        ),
    ] = None
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to blur images classified as adult content. Defaults to true. Set to false to receive unblurred output. No Pro subscription is required, and the mature filter setting in the Venice app does not affect this. The x-venice-is-blurred response header reports whether the returned image was blurred.",
            examples=[False],
        ),
    ] = True
    disable_prompt_optimization_thinking: Annotated[
        bool | None,
        Field(
            description="Skip the model's prompt-optimization thinking step for faster generation. Only supported by models with `supportsOptimizePromptThinking`; ignored by others. Omit to use the model default.",
            examples=[False],
        ),
    ] = None
    enhance_prompt: Annotated[
        bool | None,
        Field(
            description="Rewrite the edit prompt using the input images before editing to add clarifying detail. Additional credits are charged when a rewrite is generated. Adds up to ~30 seconds. When enhancement is applied, the final prompt is returned URL-encoded in the `x-venice-enhanced-prompt` response header. Defaults to false.",
            examples=[False],
        ),
    ] = None
    transparent_background: Annotated[
        bool | None,
        Field(
            description="Return the edited image with a transparent background (alpha channel). Only supported by models with `supportsTransparentBackground: true` in their constraints (see GET /api/v1/models), and requires `output_format` png or webp when set; otherwise the request is rejected. Omit or set to false to keep the model default background.",
            examples=[False],
        ),
    ] = None


class MultiEditImageMultipartRequest(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    aspect_ratio: Annotated[
        AspectRatio | None,
        Field(
            description="The aspect ratio for the output image. Use 'auto' or omit this parameter to infer the closest supported aspect ratio from the first input image when explicit sizing is required by the model.",
            examples=[969],
        ),
    ] = None
    modelId: Annotated[
        str | None,
        Field(description="The model ID to use for multi-edit.", min_length=1),
    ] = "firered-image-edit"
    output_format: Annotated[
        OutputFormat | None,
        Field(
            description="Output format for the edited image. Accepts jpeg, jpg, png, or webp. When omitted, the format is inferred from resolution: PNG for 1K edits and JPEG for 2K/4K edits, or PNG at any resolution when transparent_background is true.",
            examples=["png"],
        ),
    ] = "png"
    prompt: Annotated[
        str,
        Field(
            description='The text directions to edit or modify the image. Short, descriptive prompts work best (e.g., "remove the tree", "change the sky to sunrise"). Character limit is model specific and is listed in the promptCharacterLimit setting in the model list endpoint.',
            max_length=32768,
            min_length=1,
        ),
    ]
    images: Annotated[
        list[bytes],
        Field(
            description="Image files (minimum 1). The maximum is model-specific — see `capabilities.maxInputImages` from GET /api/v1/models. The first image is treated as the base image, and the remaining images are used as edit layers/masks.",
            min_length=1,
        ),
    ]
    quality: Annotated[
        Quality2 | None,
        Field(
            description="Output quality for supported models (e.g. GPT Image 2 / GPT Image 2 Edit). Higher values can increase the final request charge. See the model list for supported options.",
            examples=["high"],
        ),
    ] = None
    resolution: Annotated[
        str | None,
        Field(
            description='Resolution tier for the output image (e.g. "1K", "2K", "4K"). Supported values vary by model - check GET /api/v1/models for model-specific options. Defaults to "1K" when not specified.',
            examples=["1K"],
            max_length=10,
            min_length=1,
        ),
    ] = None
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to blur images classified as adult content. Defaults to true. Set to false to receive unblurred output. No Pro subscription is required, and the mature filter setting in the Venice app does not affect this. The x-venice-is-blurred response header reports whether the returned image was blurred.",
            examples=[False],
        ),
    ] = True
    disable_prompt_optimization_thinking: Annotated[
        bool | None,
        Field(
            description="Skip the model's prompt-optimization thinking step for faster generation. Only supported by models with `supportsOptimizePromptThinking`; ignored by others. Omit to use the model default.",
            examples=[False],
        ),
    ] = None
    enhance_prompt: Annotated[
        bool | None,
        Field(
            description="Rewrite the edit prompt using the input images before editing to add clarifying detail. Additional credits are charged when a rewrite is generated. Adds up to ~30 seconds. When enhancement is applied, the final prompt is returned URL-encoded in the `x-venice-enhanced-prompt` response header. Defaults to false.",
            examples=[False],
        ),
    ] = None
    transparent_background: Annotated[
        bool | None,
        Field(
            description="Return the edited image with a transparent background (alpha channel). Only supported by models with `supportsTransparentBackground: true` in their constraints (see GET /api/v1/models), and requires `output_format` png or webp when set; otherwise the request is rejected. Omit or set to false to keep the model default background.",
            examples=[False],
        ),
    ] = None


class BackgroundRemoveImageRequest1(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    image: Annotated[
        str,
        Field(
            description="The non-empty base64-encoded image to remove the background from.",
            min_length=1,
            pattern="\\S",
        ),
    ]


class BackgroundRemoveImageRequest2(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    image_url: Annotated[
        AnyUrl,
        Field(
            description="URL of the image to remove the background from.",
            examples=["https://example.com/image.jpg"],
        ),
    ]


class BackgroundRemoveImageRequest(
    RootModel[BackgroundRemoveImageRequest1 | BackgroundRemoveImageRequest2]
):
    root: Annotated[
        BackgroundRemoveImageRequest1 | BackgroundRemoveImageRequest2,
        Field(
            description="Remove the background from an image. Provide either a non-empty base64 image or an image URL.",
            examples=[{"image_url": "https://example.com/image.jpg"}],
        ),
    ]


class BackgroundRemoveImageMultipartRequest(VeniceBaseModel):
    anon_user_id: Annotated[
        str | None,
        Field(
            description="Optional identifier for the API customer's end user. Combined with the Venice user id when attributing the request to upstream providers. Distinct from the discarded OpenAI `user` field. Must be printable ASCII and must not contain `||`.",
            examples=["end-user-123"],
            max_length=128,
            min_length=1,
            pattern="^[\\x20-\\x7E]+$",
        ),
    ] = None
    image: Annotated[
        bytes,
        Field(
            description="The non-empty image file to remove the background from. File size must be less than 25MB.",
            min_length=1,
        ),
    ]


class EncodingFormat(Enum):
    float = "float"
    base64 = "base64"


class Input12(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="The string that will be turned into an embedding. Cannot be an empty string.",
            examples=["This is a test."],
            min_length=1,
            title="string",
        ),
    ]


class Input13(RootModel[list[str]]):
    root: Annotated[
        list[str],
        Field(
            description="The array of strings that will be turned into an embedding. Array must contain 2048 items or less.",
            examples=[["This is a test."]],
            max_length=2048,
            min_length=1,
            title="array",
        ),
    ]


class Model(Enum):
    text_embedding_bge_m3 = "text-embedding-bge-m3"
    text_embedding_bge_en_icl = "text-embedding-bge-en-icl"
    text_embedding_qwen3_8b = "text-embedding-qwen3-8b"
    text_embedding_qwen3_0_6b = "text-embedding-qwen3-0-6b"
    text_embedding_multilingual_e5_large_instruct = "text-embedding-multilingual-e5-large-instruct"
    text_embedding_3_small = "text-embedding-3-small"
    text_embedding_3_large = "text-embedding-3-large"
    gemini_embedding_2_preview = "gemini-embedding-2-preview"
    text_embedding_nemotron_embed_vl_1b_v2 = "text-embedding-nemotron-embed-vl-1b-v2"


class CreateEmbeddingRequestSchema(VeniceBaseModel):
    dimensions: Annotated[
        int | None,
        Field(
            description="The number of dimensions the resulting output embeddings should have.",
            ge=1,
        ),
    ] = None
    encoding_format: Annotated[
        EncodingFormat | None,
        Field(
            description="The format to return the embeddings in. Can be either `float` or `base64`.",
            examples=["float"],
        ),
    ] = "float"
    input: Annotated[
        Input12 | Input13,
        Field(
            description="Input text to embed, encoded as a string or array of strings. To embed multiple inputs in a single request, pass an array of strings. The input must not exceed the max input tokens for the model (8192 tokens), cannot be an empty string, and any array must contain 2048 items or less. Token arrays are not supported and return HTTP 400. LangChain OpenAIEmbeddings sends token arrays unless you set check_embedding_ctx_length=False.",
            examples=["The quick brown fox jumped over the lazy dog"],
        ),
    ]
    model: Annotated[
        str | Model,
        Field(
            description="ID of the model to use. You can use the List models API to see all of your available models, or see our Model overview for descriptions of them.",
            examples=["text-embedding-bge-m3"],
        ),
    ]
    user: Annotated[
        str | None,
        Field(
            description="This is an unused parameter and is discarded by Venice. It is supported solely for API compatibility with OpenAI."
        ),
    ] = None


class State(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="The content to evaluate: a plain string for text, or structured data (object/array) for things like chat logs, records, or application state.",
            examples=["Help! My payouts have been failing for 3 days."],
            min_length=1,
        ),
    ]


class State1(RootModel[list[Any]]):
    root: Annotated[
        list[Any],
        Field(
            description="The content to evaluate: a plain string for text, or structured data (object/array) for things like chat logs, records, or application state.",
            examples=["Help! My payouts have been failing for 3 days."],
            min_length=1,
        ),
    ]


class Model1(Enum):
    jev_latest = "jev-latest"
    clef = "clef"
    clef_api = "clef-api"


class Images(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="A `data:` URI for a PNG or JPEG. Remote URLs are not fetched.",
            examples=["data:image/png;base64,iVBORw0KGgo="],
            max_length=13631488,
            min_length=1,
            pattern="^data:image\\/(?:png|jpeg|jpg);base64,[A-Za-z0-9+/]+=*$",
        ),
    ]


class ContentType(Enum):
    image_png = "image/png"
    image_jpeg = "image/jpeg"
    image_jpg = "image/jpg"


class Images1(VeniceBaseModel):
    content_type: Annotated[ContentType, Field(description="MIME type of the embedded image.")]
    base64: Annotated[
        str,
        Field(
            description="Raw base64 image bytes without a data: prefix.",
            max_length=13631488,
            min_length=1,
            pattern="^[A-Za-z0-9+/]+=*$",
        ),
    ]


class Type96(Enum):
    noul = "noul"


class Instructions(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="The yes/no question to evaluate against the state.",
            examples=["Does this message convey urgency?"],
            min_length=1,
        ),
    ]


class Instructions1(RootModel[list[Any]]):
    root: Annotated[
        list[Any],
        Field(
            description="The yes/no question to evaluate against the state.",
            examples=["Does this message convey urgency?"],
            min_length=1,
        ),
    ]


class Criteria(VeniceBaseModel):
    true: Annotated[str | None, Field(description="What a yes (value near 1) means.")] = None
    false: Annotated[str | None, Field(description="What a no (value near 0) means.")] = None


class Questions(VeniceBaseModel):
    type: Type96
    instructions: Annotated[
        Instructions | dict[str, Any] | Instructions1,
        Field(
            description="The yes/no question to evaluate against the state.",
            examples=["Does this message convey urgency?"],
        ),
    ]
    criteria: Criteria | None = None


class Type97(Enum):
    choice = "choice"


class Instructions2(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="What the model should decide.",
            examples=["Which team should handle this?"],
            min_length=1,
        ),
    ]


class Instructions3(RootModel[list[Any]]):
    root: Annotated[
        list[Any],
        Field(
            description="What the model should decide.",
            examples=["Which team should handle this?"],
            min_length=1,
        ),
    ]


class Questions1(VeniceBaseModel):
    type: Type97
    instructions: Annotated[
        Instructions2 | dict[str, Any] | Instructions3,
        Field(
            description="What the model should decide.",
            examples=["Which team should handle this?"],
        ),
    ]
    criteria: Annotated[
        dict[str, str],
        Field(
            description="Map of option name to rubric description; use null when an option needs no extra detail.",
            examples=[
                {
                    "billing": "Payments, invoicing, refunds",
                    "technical": "Bugs, outages, integrations",
                }
            ],
        ),
    ]


class Type98(Enum):
    score = "score"


class Instructions4(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="What the model should rate.",
            examples=["How frustrated is the customer?"],
            min_length=1,
        ),
    ]


class Instructions5(RootModel[list[Any]]):
    root: Annotated[
        list[Any],
        Field(
            description="What the model should rate.",
            examples=["How frustrated is the customer?"],
            min_length=1,
        ),
    ]


class Questions2(VeniceBaseModel):
    type: Type98
    instructions: Annotated[
        Instructions4 | dict[str, Any] | Instructions5,
        Field(
            description="What the model should rate.",
            examples=["How frustrated is the customer?"],
        ),
    ]
    criteria: Annotated[
        list[str],
        Field(
            description="Ordered array of level descriptions, lowest to highest. At least two levels are required.",
            examples=[["Calm", "Frustrated", "Very angry"]],
            min_length=2,
        ),
    ]


class CreateDecisionRequestSchema(VeniceBaseModel):
    state: Annotated[
        State | dict[str, Any] | State1,
        Field(
            description="The content to evaluate: a plain string for text, or structured data (object/array) for things like chat logs, records, or application state.",
            examples=["Help! My payouts have been failing for 3 days."],
        ),
    ]
    model: Annotated[
        str | Model1,
        Field(
            description="ID of the decision model to use. You can use the List models API (type=decision) to see available models, or see our Model overview for descriptions of them.",
            examples=["jev-latest"],
        ),
    ]
    images: Annotated[
        list[Images | Images1] | None,
        Field(
            description="Up to 4 images the model should look at. Each entry is a `data:` URI or `{ content_type, base64 }`. Remote URLs are not fetched.",
            max_length=4,
            min_length=1,
        ),
    ] = None
    questions: Annotated[
        dict[str, Questions | Questions1 | Questions2],
        Field(
            description="Map of typed questions, keyed by an id you choose. At least one question is required. Answers come back under the same ids. Every question is evaluated in parallel and in isolation against the same state. Question ids are not sent to the model.",
            examples=[
                {
                    "is_urgent": {
                        "type": "noul",
                        "instructions": "Does this message convey urgency?",
                    }
                }
            ],
        ),
    ]


class Model2(Enum):
    tts_kokoro = "tts-kokoro"
    tts_qwen3_0_6b = "tts-qwen3-0-6b"
    tts_qwen3_1_7b = "tts-qwen3-1-7b"
    tts_xai_v1 = "tts-xai-v1"
    tts_inworld_1_5_max = "tts-inworld-1-5-max"
    tts_chatterbox_hd = "tts-chatterbox-hd"
    tts_orpheus = "tts-orpheus"
    tts_elevenlabs_turbo_v2_5 = "tts-elevenlabs-turbo-v2-5"
    tts_minimax_speech_02_hd = "tts-minimax-speech-02-hd"
    tts_gemini_3_1_flash = "tts-gemini-3-1-flash"
    tts_gradium_v1 = "tts-gradium-v1"
    tts_heygen_voice = "tts-heygen-voice"
    tts_heygen_voice_turbo = "tts-heygen-voice-turbo"


class ResponseFormat4(Enum):
    mp3 = "mp3"
    opus = "opus"
    aac = "aac"
    flac = "flac"
    wav = "wav"
    pcm = "pcm"


class CreateSpeechRequestSchema(VeniceBaseModel):
    input: Annotated[
        str,
        Field(
            description="The text to generate audio for. The maximum length is 4096 characters.",
            examples=["Hello, this is a test of the text to speech system."],
            max_length=4096,
            min_length=1,
        ),
    ]
    language: Annotated[
        str | None,
        Field(
            description="Optional language hint. Accepted values are model-specific: Qwen 3 accepts full names (English, Chinese, ...); xAI/ElevenLabs accept ISO 639-1 codes (en, ja, ...); MiniMax accepts full names. Unsupported values are silently ignored. Omit to let the model auto-detect.",
            examples=["English"],
            max_length=32,
            min_length=2,
        ),
    ] = None
    model: Annotated[
        Model2 | None,
        Field(description="The model ID of a Venice TTS model.", examples=["tts-xai-v1"]),
    ] = "tts-kokoro"
    prompt: Annotated[
        str | None,
        Field(
            description='A style prompt to control the emotion and delivery of the speech. Supported by models advertising `supportsPromptParam` (currently Qwen 3 TTS). Ignored by other models. Examples: "Very happy.", "Sad and slow.", "Excited and energetic."',
            examples=["Very happy."],
            max_length=500,
        ),
    ] = None
    response_format: Annotated[
        ResponseFormat4 | None,
        Field(
            description="Requested audio output format. Supported formats and the default when omitted are model-specific; see `model_spec.supported_formats` and `model_spec.default_format` from GET /models?type=tts. An explicit unsupported format returns HTTP 400.",
            examples=["mp3"],
        ),
    ] = None
    speed: Annotated[
        float | None,
        Field(
            description="The speed of the generated audio. Select a value from 0.25 to 4.0. 1.0 is the default.",
            examples=[1],
            ge=0.25,
            le=4.0,
        ),
    ] = 1
    streaming: Annotated[
        bool | None,
        Field(
            description="Should the content stream back sentence by sentence or be processed and returned as a complete audio file.",
            examples=[True],
        ),
    ] = False
    temperature: Annotated[
        float | None,
        Field(
            description="Sampling temperature for speech generation. Higher values produce more varied output. Supported by models advertising `supportsTemperatureParam` (Qwen 3, Orpheus, Chatterbox HD). Ignored by other models.",
            examples=[0.9],
            ge=0.0,
            le=2.0,
        ),
    ] = None
    top_p: Annotated[
        float | None,
        Field(
            description="Nucleus sampling parameter. Supported by models advertising `supportsTopPParam` (currently Qwen 3 TTS). Ignored by other models.",
            examples=[1],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    voice: Annotated[
        str | None,
        Field(
            description="The voice to use when generating the audio. The maximum length is 512 characters. Voices are model-specific: Kokoro (e.g. af_sky, af_bella, am_adam), Qwen 3 (e.g. Vivian, Serena, Dylan), xAI (26 voices, e.g. eve, ara, rex, sal, leo, luna, orion, carina), Orpheus (tara, leah, jess, leo, dan, mia, zac, zoe), Inworld (Craig, Ashley, ...), Chatterbox (Aurora, Blade, ...), ElevenLabs Turbo (Rachel, Aria, ...), MiniMax (WiseWoman, DeepVoiceMan, ...), Gradium (Emma, Kent, Mia, Maximilian, Valentina, Sergio, Elise, Leo, Alice, Davi — spanning en/de/es/fr/pt). You can also pass a cloned-voice handle (`vv_<id>`) returned by POST /v1/audio/voices to synthesize in a previously cloned voice; the handle must be paired with the same model used to create it. Models that advertise `supports_custom_voice_id` (e.g. ElevenLabs) additionally accept a raw provider Voice ID here. Using an incompatible voice returns a 400 error. Call GET /models/{id} to list voices for a specific model.",
            examples=["af_sky"],
            max_length=512,
        ),
    ] = "af_sky"


class Model3(Enum):
    nvidia_parakeet_tdt_0_6b_v3 = "nvidia/parakeet-tdt-0.6b-v3"
    openai_whisper_large_v3 = "openai/whisper-large-v3"
    fal_ai_wizper = "fal-ai/wizper"
    elevenlabs_scribe_v2 = "elevenlabs/scribe-v2"
    stt_xai_v1 = "stt-xai-v1"


class ResponseFormat5(Enum):
    json = "json"
    text = "text"


class CreateTranscriptionRequestSchema(VeniceBaseModel):
    file: Annotated[
        bytes | None,
        Field(
            description="The audio file object (not a base64 string). Supported formats: WAV, WAVE, FLAC, M4A, AAC, MP4, MP3, OGG, OGA, WEBM."
        ),
    ] = None
    model: Annotated[
        Model3 | None,
        Field(
            description="The model to use for transcription. See https://docs.venice.ai/models/overview for more information.",
            examples=["openai/whisper-large-v3"],
        ),
    ] = "nvidia/parakeet-tdt-0.6b-v3"
    response_format: Annotated[
        ResponseFormat5 | None,
        Field(
            description="The format of the transcript output, in one of these options: json, text.",
            examples=["json"],
        ),
    ] = "json"
    timestamps: Annotated[
        bool | None,
        Field(
            description="Whether to include timestamps in the response.",
            examples=[False],
        ),
    ] = False
    language: Annotated[
        str | None,
        Field(
            description='ISO 639-1 language code (e.g., "en", "es", "fr"). Optional - if not provided, the model will auto-detect the language. Note: Only supported by certain models (e.g., Whisper). Ignored by models that do not support language hints.',
            examples=["en"],
        ),
    ] = None


class Model4(Enum):
    tts_chatterbox_hd = "tts-chatterbox-hd"
    tts_minimax_speech_02_hd = "tts-minimax-speech-02-hd"


class CreateClonedVoiceRequestSchema(VeniceBaseModel):
    file: Annotated[
        bytes | None,
        Field(
            description='The voice sample audio file (multipart/form-data, field name "file"). Accepted containers depend on the selected model: `tts-chatterbox-hd` accepts MP3, WAV, FLAC, and M4A; `tts-minimax-speech-02-hd` accepts MP3 and WAV only. Recommended: a clean speech recording of at least 5–10 seconds.'
        ),
    ] = None
    model: Annotated[
        Model4 | None,
        Field(
            description="The Venice TTS model the cloned voice will be paired with. The returned voice handle is only valid against this model on POST /v1/audio/speech.",
            examples=["tts-chatterbox-hd"],
        ),
    ] = "tts-chatterbox-hd"


class ConfirmedTermsAndPrivacy(Enum):
    boolean_True = True


class ConfirmedLegalRight(Enum):
    boolean_True = True


class ConfirmedScreeningAcknowledged(Enum):
    boolean_True = True


class Seedance(VeniceBaseModel):
    confirmed_terms_and_privacy: Annotated[
        ConfirmedTermsAndPrivacy,
        Field(
            description="Confirms acceptance of the current provider policy text returned in the needs_consent response.",
            examples=[True],
        ),
    ]
    confirmed_legal_right: Annotated[
        ConfirmedLegalRight,
        Field(
            description="Confirms the API user has the legal right to use the submitted media.",
            examples=[True],
        ),
    ]
    confirmed_screening_acknowledged: Annotated[
        ConfirmedScreeningAcknowledged,
        Field(
            description="Acknowledges that submitted media may be screened before processing.",
            examples=[True],
        ),
    ]


class Consents(VeniceBaseModel):
    seedance: Seedance | None = None


class Duration(Enum):
    field_1s = "1s"
    field_2s = "2s"
    field_3s = "3s"
    field_4s = "4s"
    field_5s = "5s"
    field_6s = "6s"
    field_7s = "7s"
    field_8s = "8s"
    field_9s = "9s"
    field_10s = "10s"
    field_11s = "11s"
    field_12s = "12s"
    field_13s = "13s"
    field_14s = "14s"
    field_15s = "15s"
    field_16s = "16s"
    field_17s = "17s"
    field_18s = "18s"
    field_19s = "19s"
    field_20s = "20s"
    field_21s = "21s"
    field_22s = "22s"
    field_23s = "23s"
    field_24s = "24s"
    field_25s = "25s"
    field_26s = "26s"
    field_27s = "27s"
    field_28s = "28s"
    field_29s = "29s"
    field_30s = "30s"
    field_1 = "-1"
    field_1_gen = "1 gen"
    auto = "auto"
    Auto = "Auto"


class AspectRatio3(Enum):
    field_61 = 61
    field_121 = 121
    field_123 = 123
    field_182 = 182
    field_184 = 184
    field_243 = 243
    field_245 = 245
    field_304 = 304
    field_556 = 556
    field_561 = 561
    field_969 = 969
    field_1269 = 1269
    adaptive = "adaptive"
    auto = "auto"


class OmniReferenceTaskType(Enum):
    auto = "auto"
    reference = "reference"
    edit = "edit"
    extend = "extend"


class Resolution(Enum):
    field_256p = "256p"
    field_360p = "360p"
    field_480p = "480p"
    field_540p = "540p"
    field_580p = "580p"
    field_720p = "720p"
    field_768p = "768p"
    field_1080p = "1080p"
    field_1440p = "1440p"
    field_2160p = "2160p"
    field_2k = "2k"
    field_4k = "4k"
    field_1x = "1x"
    field_2x = "2x"
    field_4x = "4x"
    field_2K = "2K"
    field_480P = "480P"
    field_768P = "768P"
    field_1080P = "1080P"
    true_1080p = "true_1080p"


class UpscaleFactor(IntEnum):
    integer_1 = 1
    integer_2 = 2
    integer_4 = 4


class OutputFormat4(Enum):
    mp4 = "mp4"
    prores = "prores"


class SlowdownFactor(IntEnum):
    integer_1 = 1
    integer_2 = 2
    integer_4 = 4
    integer_8 = 8


class CameraTrajectoryItem(VeniceBaseModel):
    time: Annotated[float, Field(ge=0.0, le=1.0)]
    azimuth: float
    elevation: Annotated[float, Field(ge=-90.0, le=90.0)]
    distance: Annotated[float, Field(gt=0.0)]


class Element(VeniceBaseModel):
    frontal_image_url: str | None = None
    reference_image_urls: Annotated[list[str] | None, Field(max_length=3)] = None
    video_url: str | None = None


class Keyframe(VeniceBaseModel):
    image_url: str
    frame_index: Annotated[int, Field(ge=0)]


class QueueVideoRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model to use for video generation.",
            examples=["seedance-2-0-text-to-video-basic"],
        ),
    ]
    consents: Annotated[
        Consents | None,
        Field(
            description="Optional provider-specific consent attestations. Required only for models that return a needs_consent response."
        ),
    ] = None
    prompt: Annotated[
        str | None,
        Field(
            description="The prompt to use for video generation. Required for most models; optional for H3 Max Multi-Angle. The maximum length varies by model (default 2500 characters, up to 32000 for some models).",
            examples=["Commerce being conducted in the city of Venice, Italy."],
            max_length=32000,
            min_length=1,
        ),
    ] = None
    negative_prompt: Annotated[
        str | None,
        Field(
            description="Optional negative prompt. The maximum length varies by model (default 2500 characters, up to 32000 for some models).",
            examples=["low resolution, error, worst quality, low quality, defects"],
            max_length=32000,
        ),
    ] = None
    duration: Annotated[
        Duration,
        Field(
            description="The duration of the video to generate. Available options vary by model. For Seedance 2.5 reference-to-video edit jobs, `-1` or `auto` matches output length to the source clip (requires reference_video_urls on queue, or reference_video_total_duration on quote; source must be 4–30s).",
            examples=["10s"],
        ),
    ]
    aspect_ratio: Annotated[
        AspectRatio3 | None,
        Field(
            description="The aspect ratio of the video. Available options vary by model. Some models do not support aspect_ratio. For Seedance 2.x reference-to-video edit/extend, `adaptive` or `auto` matches output aspect ratio to the source clip (requires reference_video_urls on queue, or reference_video_total_duration on quote).",
            examples=[969],
        ),
    ] = None
    omni_reference_task_type: Annotated[
        OmniReferenceTaskType | None,
        Field(
            description="Optional Seedance 2.5 reference-to-video task-type hint forwarded to BytePlus (`auto` | `reference` | `edit` | `extend`). Aliases `editing`→`edit` and `extension`→`extend` are accepted on the queue API. Pre-guides classification to reduce async TaskTypeConstraint errors. The prompt must still match the chosen type. When omitted, Venice infers from the prompt if reference_video_urls are present. Not supported on other models.",
            examples=["edit"],
        ),
    ] = None
    resolution: Annotated[
        Resolution | None,
        Field(
            description="The resolution of the video. Available options vary by model. Some models do not support resolution. Use upscale_factor for upscale models.",
            examples=["720p"],
        ),
    ] = None
    upscale_factor: Annotated[
        UpscaleFactor | None,
        Field(
            description="For upscale models only. 1 = quality enhancement, 2 = double resolution (default), 4 = quadruple.",
            examples=[2],
        ),
    ] = 2
    enhancement_model: Annotated[
        str | None,
        Field(
            description="For enhancement models only. The provider-side enhancement model. Available values are listed per model in GET /models constraints.topaz.models.",
            examples=["Proteus"],
        ),
    ] = None
    target_fps: Annotated[
        int | None,
        Field(
            description="For enhancement models only. Target FPS for frame interpolation (16-120). Doubles the price on upscaling endpoints when ≥48; scales linearly on interpolation. Omit to keep the source frame rate.",
            examples=[60],
        ),
    ] = None
    softness: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Softness level (1-5, sharpest to softest).",
            examples=[3],
            ge=1.0,
            le=5.0,
        ),
    ] = None
    creativity: Annotated[
        float | None,
        Field(
            description="For enhancement models only. How much new detail the model invents (0.0-1.0).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    realism: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Bias generated detail toward photorealism (0.0-1.0).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    sharp: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Output sharpness (0.0 softens, 0.5 neutral, 1.0 strong).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    compression: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Compression artifact removal level (0.0-1.0).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    noise: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Noise reduction level (0.0-1.0).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    halo: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Halo reduction level (0.0-1.0).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    grain: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Film grain amount (0.0-0.1).",
            examples=[0],
            ge=0.0,
            le=0.1,
        ),
    ] = None
    recover_detail: Annotated[
        float | None,
        Field(
            description="For enhancement models only. Recover original detail level (0.0-1.0).",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    h264_output: Annotated[
        bool | None,
        Field(
            description="For enhancement models only. Output H.264 instead of the default H.265.",
            examples=[False],
        ),
    ] = None
    output_format: Annotated[
        OutputFormat4 | None,
        Field(
            description="For enhancement models only (SDR-to-HDR). Output container: mp4 (10-bit H265 HDR10) or prores (10-bit ProRes).",
            examples=["mp4"],
        ),
    ] = None
    slowdown_factor: Annotated[
        SlowdownFactor | None,
        Field(
            description="For enhancement models only (frame interpolation). Slow-motion factor: 2 makes the output twice as long at the target FPS, up to 8x. Multiplies the billed duration.",
            examples=[1],
        ),
    ] = None
    audio: Annotated[
        bool | None,
        Field(
            description="For models which support audio generation and configuration. Defaults to true.",
            examples=[True],
        ),
    ] = True
    camera_trajectory: Annotated[
        list[CameraTrajectoryItem] | None,
        Field(
            description="For H3 Max Multi-Angle only. 2–12 camera keyframes with strictly increasing normalized time (0–1), azimuth in degrees (signed; total absolute travel at most 32 turns), elevation in degrees (−90 to 90), and positive distance relative to the initial camera (1 = unchanged). Omit to leave the camera path to the model. Requires image_url; aspect ratio follows that image.",
            examples=[
                [
                    {"time": 0, "azimuth": 0, "elevation": 0, "distance": 1},
                    {"time": 1, "azimuth": 45, "elevation": 10, "distance": 1},
                ]
            ],
            max_length=12,
            min_length=2,
        ),
    ] = None
    image_url: Annotated[
        str | None,
        Field(
            description="For image-to-video models, the reference image. Must be a URL (http/https) or a data URL (data:image/...).",
            examples=["data:image/png;base64,iVBORw0K..."],
        ),
    ] = None
    end_image_url: Annotated[
        str | None,
        Field(
            description="For models that support end images or transitions, the end frame image. Must be a URL or data URL.",
            examples=["data:image/png;base64,iVBORw0K..."],
        ),
    ] = None
    image_strength: Annotated[
        float | None,
        Field(
            description="How strongly the input image guides an image-to-video generation, from 0 to 1. Supported on models that declare image strength. Omitted values use the provider default (1). Does not change the quoted price.",
            examples=[1],
            ge=0.0,
            le=1.0,
        ),
    ] = None
    audio_url: Annotated[
        str | None,
        Field(
            description="For models that support audio input, background music. Must be a URL or data URL. Supported: WAV, MP3. Max: 30s, 15MB.",
            examples=["data:audio/mpeg;base64,SUQzBAA..."],
        ),
    ] = None
    video_url: Annotated[
        str | None,
        Field(
            description="For models that support video input (video-to-video, upscale). Must be a URL or data URL. Supported: MP4, MOV, WebM.",
            examples=["data:video/mp4;base64,AAAAFGZ0eXA..."],
        ),
    ] = None
    reference_image_urls: Annotated[
        list[str] | None,
        Field(
            description="For models with reference image support, up to 30 images for character/style consistency. Each must be a URL or data URL.",
            examples=[["data:image/png;base64,iVBORw0K..."]],
            max_length=30,
        ),
    ] = None
    reference_video_urls: Annotated[
        list[str] | None,
        Field(
            description='For models with reference video support (e.g. Seedance 2.0 R2V), up to 10 reference video URLs (`role: "reference_video"`) used to inherit subject motion, camera movement, and overall style. Per-clip 2–15 s, .mp4 or .mov, ≤50 MB; aggregate duration ≤15 s. Each must be a URL or data URL.',
            examples=[["https://example.com/reference-clip.mp4"]],
            max_length=10,
        ),
    ] = None
    reference_audio_urls: Annotated[
        list[str] | None,
        Field(
            description='For models with reference audio support (e.g. Seedance 2.0 R2V), up to 10 reference audio URLs (`role: "reference_audio"`) used as donors for vocal timbre, narration, or sound effects. Per-clip 2–15 s, .wav or .mp3; aggregate duration ≤15 s. Must be paired with at least one reference image or reference video — audio-only Reference workflows are rejected at validation. Each must be a URL or data URL.',
            examples=[["data:audio/mpeg;base64,SUQzBAAAAAA..."]],
            max_length=10,
        ),
    ] = None
    reference_document_urls: Annotated[
        list[str] | None,
        Field(
            description='For models with document / webpage Omni-Reference (Wan 3.0), up to 1 URL. Document files and public webpage URLs are fetched by Venice and forwarded as `type: "file"` (≤100 MB). Each must be a URL or data URL.',
            examples=[["https://example.com/brief.pdf"]],
            max_length=1,
        ),
    ] = None
    elements: Annotated[
        list[Element] | None,
        Field(
            description="For models with advanced element support (e.g., Kling O3 R2V). Up to 4 elements defining characters/objects. Reference in prompt as @Element1, @Element2, etc.",
            examples=[
                [
                    {
                        "frontal_image_url": "data:image/png;base64,iVBORw0K...",
                        "reference_image_urls": ["data:image/png;base64,iVBORw0K..."],
                    }
                ]
            ],
            max_length=4,
        ),
    ] = None
    scene_image_urls: Annotated[
        list[str] | None,
        Field(
            description="For models with advanced element support. Up to 4 scene reference images. Reference in prompt as @Image1, @Image2, etc.",
            examples=[["data:image/png;base64,iVBORw0K..."]],
            max_length=4,
        ),
    ] = None
    keyframes: Annotated[
        list[Keyframe] | None,
        Field(
            description="For keyframe-driven models. Up to 10 keyframe images pinned to frame positions in the generated 24 fps video. Each frame_index must be unique and no greater than duration × 24.",
            examples=[
                [
                    {
                        "image_url": "data:image/png;base64,iVBORw0K...",
                        "frame_index": 0,
                    },
                    {
                        "image_url": "data:image/png;base64,iVBORw0K...",
                        "frame_index": 120,
                    },
                ]
            ],
            max_length=10,
        ),
    ] = None


class QuoteVideoRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model to get a price quote for.",
            examples=["seedance-2-0-text-to-video-basic"],
        ),
    ]
    duration: Annotated[
        Duration,
        Field(
            description="The duration of the video. Available options vary by model. For Seedance 2.5 reference-to-video edit jobs, `-1` or `auto` matches output length to the source clip (requires reference_video_urls on queue, or reference_video_total_duration on quote; source must be 4–30s).",
            examples=["10s"],
        ),
    ]
    aspect_ratio: Annotated[
        AspectRatio3 | None,
        Field(
            description="The aspect ratio. Required for some models with megapixel-rate pricing. For Seedance 2.x reference-to-video edit/extend, `adaptive` or `auto` matches output aspect ratio to the source clip (requires reference_video_urls on queue, or reference_video_total_duration on quote).",
            examples=[969],
        ),
    ] = None
    resolution: Annotated[
        Resolution | None,
        Field(
            description="The resolution. Required for models with duration-resolution-rate pricing.",
            examples=["720p"],
        ),
    ] = None
    upscale_factor: Annotated[
        UpscaleFactor | None,
        Field(
            description="For upscale models only. The upscale multiplier the queue request will use (1, 2 or 4); the quote bills the output tier of source height × factor. Defaults to the model's default factor.",
            examples=[2],
        ),
    ] = 2
    enhancement_model: Annotated[
        str | None,
        Field(
            description="For enhancement models only. The provider-side enhancement model. Available values are listed per model in GET /models constraints.topaz.models.",
            examples=["Proteus"],
        ),
    ] = None
    target_fps: Annotated[
        int | None,
        Field(
            description="For enhancement models only. Target FPS for frame interpolation (16-120). Doubles the price on upscaling endpoints when ≥48; scales linearly on interpolation. Omit to keep the source frame rate.",
            examples=[60],
        ),
    ] = None
    slowdown_factor: Annotated[
        SlowdownFactor | None,
        Field(
            description="For enhancement models only (frame interpolation). Slow-motion factor: 2 makes the output twice as long at the target FPS, up to 8x. Multiplies the billed duration.",
            examples=[1],
        ),
    ] = None
    audio: Annotated[
        bool | None,
        Field(
            description="For models which support audio generation and configuration. Defaults to true.",
            examples=[True],
        ),
    ] = True
    video_url: Annotated[
        str | None,
        Field(
            description="For upscale models, the video to upscale. Required to auto-detect duration for pricing.",
            examples=["data:video/mp4;base64,AAAAFGZ0eXA..."],
        ),
    ] = None
    reference_video_total_duration: Annotated[
        float | None,
        Field(
            description="For R2V models (e.g. Seedance 2.0 / 2.5 R2V), the aggregate duration in seconds of all reference videos to include in the quote (max 150s; per-clip and family caps vary by model). When provided, the quote reflects the BytePlus 'input with video' rate tier and the (input+output)×pixels token formula. Required when quoting Seedance source-matched duration (`-1`/`auto`) or aspect ratio (`adaptive`/`auto`). When omitted for ordinary fixed-duration quotes, the quote returns the no-reference baseline.",
            examples=[5],
            ge=0.0,
        ),
    ] = None


class CompleteVideoRequest(VeniceBaseModel):
    model: Annotated[
        str | None,
        Field(
            deprecated=True,
            description="Ignored. The queued video identifies its own model.",
            examples=["video-model-123"],
        ),
    ] = None
    queue_id: Annotated[
        str,
        Field(
            description="The ID of the video generation request.",
            examples=["123e4567-e89b-12d3-a456-426614174000"],
        ),
    ]


class RetrieveVideoRequest(VeniceBaseModel):
    model: Annotated[
        str | None,
        Field(
            deprecated=True,
            description="Ignored. The queued video identifies its own model.",
            examples=["video-model-123"],
        ),
    ] = None
    queue_id: Annotated[
        str,
        Field(
            description="The ID of the video generation request.",
            examples=["123e4567-e89b-12d3-a456-426614174000"],
        ),
    ]
    delete_media_on_completion: Annotated[
        bool | None,
        Field(
            description="If true, the video media will be deleted from storage after the request is completed. If false, you can use the complete endpoint to remove the media once you have successfully downloaded the video.",
            examples=[False],
        ),
    ] = False


class TextParserRequest(VeniceBaseModel):
    file: Annotated[
        bytes | None,
        Field(
            description="The document file to parse. Supported formats: PDF, EPUB, DOCX, PPTX, XLSX, plain text, Markdown, CSV, JSON, and most source-code files (e.g., .py, .js, .ts, .c, .cpp, .java, .go, .rs, .ps1, .sh, .yaml, .sql). Maximum size: 25MB."
        ),
    ] = None
    response_format: Annotated[
        ResponseFormat5 | None,
        Field(
            description='The format of the response output. "json" returns structured JSON, "text" returns only the extracted text.',
            examples=["json"],
        ),
    ] = "json"


class TextParserResponse(VeniceBaseModel):
    text: Annotated[str, Field(description="The extracted text content from the document.")]
    tokens: Annotated[float, Field(description="The token count of the extracted text.")]


class DurationSeconds(RootModel[int]):
    root: Annotated[
        int,
        Field(
            description="Optional duration hint in seconds. Only supported for models that expose duration metadata via `/models`. Accepts either an integer or a numeric string. If omitted, the model default duration is used when available.",
            examples=[60],
            gt=0,
        ),
    ]


class DurationSeconds1(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="Optional duration hint in seconds. Only supported for models that expose duration metadata via `/models`. Accepts either an integer or a numeric string. If omitted, the model default duration is used when available.",
            examples=[60],
            pattern="^\\d+$",
        ),
    ]


class QueueAudioRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model to use for audio generation. Voice-changer models are not supported here; use the `/api/v1/audio/voice-changer` endpoints instead.",
            examples=["elevenlabs-music"],
        ),
    ]
    prompt: Annotated[
        str,
        Field(
            description="The prompt describing the audio to generate. Minimum and maximum prompt lengths vary by model; inspect `/models` for `min_prompt_length` and `prompt_character_limit`.",
            examples=["A warm spoken narration introducing a product launch."],
            min_length=1,
        ),
    ]
    lyrics_prompt: Annotated[
        str | None,
        Field(
            description="Optional lyrics/text for lyric-capable models. Required when `/models` reports `lyrics_required=true`; unsupported when `/models` reports `supports_lyrics=false`.",
            examples=["Verse 1: Walking through the city lights..."],
        ),
    ] = None
    duration_seconds: Annotated[
        DurationSeconds | DurationSeconds1 | None,
        Field(
            description="Optional duration hint in seconds. Only supported for models that expose duration metadata via `/models`. Accepts either an integer or a numeric string. If omitted, the model default duration is used when available.",
            examples=[60],
        ),
    ] = None
    force_instrumental: Annotated[
        bool | None,
        Field(
            description="Optional instrumental toggle. Only supported when `/models` reports `supports_force_instrumental=true`.",
            examples=[False],
        ),
    ] = None
    lyrics_optimizer: Annotated[
        bool | None,
        Field(
            description="When enabled, auto-generates lyrics from the prompt. Only supported when `/models` reports `supports_lyrics_optimizer=true`. lyrics_prompt must be empty when this is true.",
            examples=[False],
        ),
    ] = None
    loop: Annotated[
        bool | None,
        Field(
            description="Render the clip so its end splices back into its start without an audible seam. Only supported when `/models` reports `supports_loop=true`.",
            examples=[False],
        ),
    ] = None
    voice: Annotated[
        str | None,
        Field(
            description="Optional voice selection for voice-enabled models. See `/models?type=music` for the model's supported `voices` and `default_voice`.",
            examples=["Aria"],
        ),
    ] = None
    language_code: Annotated[
        str | None,
        Field(
            description="Optional ISO 639-1 language code. Only supported when `/models` reports `supports_language_code=true`.",
            examples=["en"],
        ),
    ] = None
    speed: Annotated[
        float | None,
        Field(
            description="Optional audio speed multiplier. Only supported when `/models` reports `supports_speed=true`; use the model-specific `min_speed` and `max_speed` values.",
            examples=[1],
            ge=0.25,
            le=4.0,
        ),
    ] = None


class DurationSeconds2(RootModel[int]):
    root: Annotated[
        int,
        Field(
            description="Optional duration hint in seconds. Only supported for models that expose duration metadata via `/models`. Accepts either an integer or a numeric string. If omitted, the model default duration is used when available.",
            examples=[60],
            gt=0,
        ),
    ]


class DurationSeconds3(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="Optional duration hint in seconds. Only supported for models that expose duration metadata via `/models`. Accepts either an integer or a numeric string. If omitted, the model default duration is used when available.",
            examples=[60],
            pattern="^\\d+$",
        ),
    ]


class QuoteAudioRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model to get a price quote for. Voice-changer models are not supported here; use `/api/v1/audio/voice-changer/quote` instead.",
            examples=["elevenlabs-music"],
        ),
    ]
    duration_seconds: Annotated[
        DurationSeconds2 | DurationSeconds3 | None,
        Field(
            description="Optional duration hint in seconds. Only supported for models that expose duration metadata via `/models`. Accepts either an integer or a numeric string. If omitted, the model default duration is used when available.",
            examples=[60],
        ),
    ] = None
    character_count: Annotated[
        int | None,
        Field(
            description="Optional character count for character-based pricing models. Required when the selected model uses `pricing.per_thousand_characters` in `/models`.",
            examples=[100],
            gt=0,
        ),
    ] = None


class CompleteAudioRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The ID of the model used for audio generation. Voice-changer models are not supported on `/api/v1/audio/retrieve` or `/api/v1/audio/complete`; use the `/api/v1/audio/voice-changer` endpoints instead.",
            examples=["elevenlabs-music"],
        ),
    ]
    queue_id: Annotated[
        str,
        Field(
            description="The ID of the audio generation request. Use this to poll for status and retrieve the result.",
            examples=["123e4567-e89b-12d3-a456-426614174000"],
        ),
    ]


class RetrieveAudioRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The ID of the model used for audio generation. Voice-changer models are not supported on `/api/v1/audio/retrieve` or `/api/v1/audio/complete`; use the `/api/v1/audio/voice-changer` endpoints instead.",
            examples=["elevenlabs-music"],
        ),
    ]
    queue_id: Annotated[
        str,
        Field(
            description="The ID of the audio generation request. Use this to poll for status and retrieve the result.",
            examples=["123e4567-e89b-12d3-a456-426614174000"],
        ),
    ]
    delete_media_on_completion: Annotated[
        bool | None,
        Field(
            description="If true, the audio media will be deleted from storage after the request is completed. If false, you can use the complete endpoint to remove the media once you have successfully downloaded the audio.",
            examples=[False],
        ),
    ] = False


class QueueVoiceChangerRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The voice-changer model to run. Models that are not voice changers are not supported here; use the `/api/v1/audio` endpoints instead.",
            examples=["elevenlabs-voice-changer"],
        ),
    ]
    file: Annotated[
        bytes | None,
        Field(
            description='The source recording (multipart/form-data, field name "file"). Accepted containers are listed per model as `accepted_audio_formats` in /models. Mutually exclusive with `audio_url`.'
        ),
    ] = None
    audio_url: Annotated[
        str | None,
        Field(
            description="Publicly reachable http(s) URL of the source recording. Venice fetches and validates the bytes itself and forwards only those bytes to the provider, so the URL is never handed onward. Mutually exclusive with the multipart `file` field.",
            examples=["https://example.com/source-recording.mp3"],
        ),
    ] = None
    voice: Annotated[
        str | None,
        Field(
            description="The target voice: one of the model’s `voices` from /models, or a provider Voice ID when the model reports `supports_custom_voice_id`. Defaults to the model’s `default_voice`.",
            examples=["Aria"],
        ),
    ] = None
    remove_background_noise: Annotated[
        bool | None,
        Field(
            description="Strip background noise from the source recording before conversion.",
            examples=[False],
        ),
    ] = None
    seed: Annotated[
        int | None,
        Field(
            description="Seed for reproducible output. Omit for a non-deterministic result.",
            examples=[42],
            ge=0,
        ),
    ] = None


class DurationSeconds4(RootModel[int]):
    root: Annotated[
        int,
        Field(
            description="Length of the source recording in seconds. Voice Changer preserves timing, so the source length is the billable quantity, priced in whole-minute tiers. This is an estimate: the charge is computed from the length Venice measures server-side when the recording is queued. The per-model maximum is published as `max_source_audio_duration_seconds` in /models.",
            examples=[60],
            gt=0,
        ),
    ]


class DurationSeconds5(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="Length of the source recording in seconds. Voice Changer preserves timing, so the source length is the billable quantity, priced in whole-minute tiers. This is an estimate: the charge is computed from the length Venice measures server-side when the recording is queued. The per-model maximum is published as `max_source_audio_duration_seconds` in /models.",
            examples=[60],
            pattern="^\\d+$",
        ),
    ]


class QuoteVoiceChangerRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The voice-changer model to price. Models that are not voice changers are not supported here; use `/api/v1/audio/quote` instead.",
            examples=["elevenlabs-voice-changer"],
        ),
    ]
    duration_seconds: Annotated[
        DurationSeconds4 | DurationSeconds5,
        Field(
            description="Length of the source recording in seconds. Voice Changer preserves timing, so the source length is the billable quantity, priced in whole-minute tiers. This is an estimate: the charge is computed from the length Venice measures server-side when the recording is queued. The per-model maximum is published as `max_source_audio_duration_seconds` in /models.",
            examples=[60],
        ),
    ]


class CompleteVoiceChangerRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model that is running the conversion. Only voice-changer models are accepted on the `/api/v1/audio/voice-changer` endpoints.",
            examples=["elevenlabs-voice-changer"],
        ),
    ]
    queue_id: Annotated[
        str,
        Field(
            description="Pass this to /audio/voice-changer/retrieve to poll for the converted audio, and to /audio/voice-changer/complete when finished.",
            examples=["0190f2c4-9c1e-7a3b-8f42-2c9d5e7a1b34"],
        ),
    ]


class RetrieveVoiceChangerRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model that is running the conversion. Only voice-changer models are accepted on the `/api/v1/audio/voice-changer` endpoints.",
            examples=["elevenlabs-voice-changer"],
        ),
    ]
    queue_id: Annotated[
        str,
        Field(
            description="Pass this to /audio/voice-changer/retrieve to poll for the converted audio, and to /audio/voice-changer/complete when finished.",
            examples=["0190f2c4-9c1e-7a3b-8f42-2c9d5e7a1b34"],
        ),
    ]
    delete_media_on_completion: Annotated[
        bool | None,
        Field(
            description="Release the provider-held media as soon as this call returns the audio, so a separate /audio/voice-changer/complete call is unnecessary. The audio cannot be retrieved again afterwards.",
            examples=[False],
        ),
    ] = False


class ConsumptionCurrency(Enum):
    USD = "USD"
    VCU = "VCU"
    DIEM = "DIEM"
    BUNDLED_CREDITS = "BUNDLED_CREDITS"
    EARNED_CREDITS = "EARNED_CREDITS"


class Balances(VeniceBaseModel):
    diem: Annotated[
        float,
        Field(
            description="Remaining DIEM balance for current epoch. Null if not staking.",
            examples=[90.5],
        ),
    ]
    usd: Annotated[
        float,
        Field(
            description="USD balance, net of pending holds. Negative when the account owes USD from earlier usage, or while a pending hold exceeds the posted USD balance, until the hold is released. Null when zero.",
            examples=[25],
        ),
    ]
    bundledCredits: Annotated[
        float,
        Field(
            description="Remaining bundled credits balance. Null if not available.",
            examples=[10],
        ),
    ]
    earnedCredits: Annotated[
        float,
        Field(
            description="Remaining earned credits balance. Null if not available.",
            examples=[5],
        ),
    ]


class BillingBalanceResponse(VeniceBaseModel):
    canConsume: Annotated[
        bool,
        Field(
            description="Whether the user has sufficient balance to make API requests",
            examples=[True],
        ),
    ]
    consumptionCurrency: Annotated[
        ConsumptionCurrency,
        Field(
            description="The currency that will be used for consumption (DIEM, EARNED_CREDITS, BUNDLED_CREDITS or USD)",
            examples=["DIEM"],
        ),
    ]
    balances: Balances
    diemEpochAllocation: Annotated[
        float,
        Field(
            description="Total DIEM allocation for the current epoch (from staking). Use with balances.diem to calculate usage percentage.",
            examples=[100],
        ),
    ]


class BillingUsageAnalyticsRequest(VeniceBaseModel):
    lookback: Annotated[
        str | None,
        Field(
            description='Lookback period for usage data. Format: number followed by "d" (e.g., "7d", "30d"). Maximum: 90d',
            examples=["7d"],
            pattern="^[1-9]\\d*d$",
        ),
    ] = "7d"
    startDate: Annotated[
        str | None,
        Field(
            description="Start date for filtering records (YYYY-MM-DD). If provided, endDate is also required.",
            examples=["2024-01-01"],
            pattern="^\\d{4}-\\d{2}-\\d{2}$",
        ),
    ] = None
    endDate: Annotated[
        str | None,
        Field(
            description="End date for filtering records (YYYY-MM-DD). If provided, startDate is also required.",
            examples=["2024-01-31"],
            pattern="^\\d{4}-\\d{2}-\\d{2}$",
        ),
    ] = None


class ByDateItem(VeniceBaseModel):
    date: Annotated[str, Field(description="Date in YYYY-MM-DD format", examples=["2024-01-15"])]
    USD: Annotated[float, Field(description="Total USD usage for this date")]
    DIEM: Annotated[float, Field(description="Total DIEM usage for this date")]


class BreakdownItem(VeniceBaseModel):
    type: Annotated[
        str,
        Field(description='Token type (e.g., "Input", "Output", "Cache Read", "Cache Write")'),
    ]
    usd: Annotated[float, Field(description="USD amount for this breakdown")]
    diem: Annotated[float, Field(description="DIEM amount for this breakdown")]
    units: Annotated[float, Field(description="Number of units for this breakdown")]


class ByModelItem(VeniceBaseModel):
    modelName: Annotated[str, Field(description="Display name of the model", examples=["GLM 5.1"])]
    unitType: Annotated[
        str,
        Field(
            description="Type of units (tokens, images, chars, minutes, seconds)",
            examples=["tokens"],
        ),
    ]
    modelType: Annotated[
        str,
        Field(description="Type of model (LLM, IMAGE, TTS, ASR, VIDEO)", examples=["LLM"]),
    ]
    totalUsd: Annotated[float, Field(description="Total USD usage for this model")]
    totalDiem: Annotated[float, Field(description="Total DIEM usage for this model")]
    totalUnits: Annotated[float, Field(description="Total units consumed for this model")]
    breakdown: Annotated[
        list[BreakdownItem] | None,
        Field(description="Breakdown by token type (only present if multiple types)"),
    ] = None


class ByKeyItem(VeniceBaseModel):
    apiKeyId: Annotated[str, Field(description="API key ID, or null if usage was from web app")]
    description: Annotated[
        str,
        Field(
            description='API key description or "Web App"',
            examples=["My Production Key"],
        ),
    ]
    totalUsd: Annotated[float, Field(description="Total USD usage for this key")]
    totalDiem: Annotated[float, Field(description="Total DIEM usage for this key")]
    totalUnits: Annotated[float, Field(description="Total units consumed for this key")]


class BillingUsageAnalyticsResponse(VeniceBaseModel):
    lookback: Annotated[
        str,
        Field(
            description='The lookback period used for the query. Either "Nd" format or "startDate:endDate" format.',
            examples=["7d"],
        ),
    ]
    byDate: Annotated[
        list[ByDateItem],
        Field(description="Daily usage totals for the requested period"),
    ]
    byModel: Annotated[
        list[ByModelItem],
        Field(description="Usage breakdown by model, sorted by total spend (highest first)"),
    ]
    byModelDaily: Annotated[
        list[dict[str, float]],
        Field(
            description='Daily chart data for top 8 models. Each entry has "date" (timestamp) plus model names as keys.'
        ),
    ]
    topModels: Annotated[
        list[str],
        Field(description="Names of the top 8 models by usage (for chart legends)"),
    ]
    byKey: Annotated[
        list[ByKeyItem],
        Field(description="Usage breakdown by API key, sorted by total spend (highest first)"),
    ]
    byKeyDaily: Annotated[
        list[dict[str, float]],
        Field(
            description='Daily chart data for top 8 API keys. Each entry has "date" (timestamp) plus key descriptions as keys.'
        ),
    ]
    topKeyNames: Annotated[
        list[str],
        Field(description="Descriptions of the top 8 API keys by usage (for chart legends)"),
    ]


class Currency(Enum):
    USD = "USD"
    DIEM = "DIEM"
    BUNDLED_CREDITS = "BUNDLED_CREDITS"
    EARNED_CREDITS = "EARNED_CREDITS"


class BillingUsageHistoryRequest(VeniceBaseModel):
    currency: Annotated[
        Currency | None,
        Field(description="Filter by consumable currency", examples=["USD"]),
    ] = None
    cursor: Annotated[
        str | None,
        Field(
            description="Opaque continuation token from a previous response's nextCursor. The cursor carries the filters of the walk it continues, so no filter parameters may be sent alongside it.",
            examples=["AZq3fK9tXhIVDm2j4vN8cQwYt1sB6uEoLxRgPzKaJdHfM5nC7yW0K3w"],
            max_length=512,
            pattern="^[A-Za-z0-9_-]+$",
        ),
    ] = None
    endTimestamp: Annotated[
        AwareDatetime | None,
        Field(
            description='Exclusive upper bound on entry timestamps (ISO 8601 UTC, "Z" suffix). Must be later than startTimestamp; consecutive windows sharing a boundary walk the history without gaps or overlaps. Carried forward by the cursor.',
            examples=["2026-07-01T00:00:00Z"],
            max_length=40,
        ),
    ] = None
    pageSize: Annotated[
        int | None,
        Field(
            description="Number of entries per page. Carried forward by the cursor.",
            examples=[1000],
            ge=10,
            le=1000,
        ),
    ] = 1000
    startTimestamp: Annotated[
        AwareDatetime | None,
        Field(
            description='Inclusive lower bound on entry timestamps (ISO 8601 UTC, "Z" suffix). First page only: a continuation resumes from the cursor position instead.',
            examples=["2026-06-01T00:00:00Z"],
            max_length=40,
        ),
    ] = None


class InferenceDetails(VeniceBaseModel):
    completionTokens: Annotated[
        int,
        Field(
            description="Number of tokens used in the completion. null for non-LLM usage or when the count was not recorded.",
            ge=0,
        ),
    ]
    inferenceExecutionTime: Annotated[
        int,
        Field(
            description="Time taken for inference execution in milliseconds. null when the timing was not recorded.",
            ge=0,
        ),
    ]
    promptTokens: Annotated[
        int,
        Field(
            description="Number of tokens requested in the prompt. null for non-LLM usage or when the count was not recorded.",
            ge=0,
        ),
    ]
    requestId: Annotated[str, Field(description="Unique identifier for the inference request")]


class Datum(VeniceBaseModel):
    amount: Annotated[
        float, Field(description="The total amount charged for the billing usage entry")
    ]
    apiKeyId: Annotated[
        UUID,
        Field(
            description="ID of the API key the entry was charged to, matching the id returned by /api_keys. null when the entry was not charged to an API key: usage from the Venice web app, and non-usage entries such as credit purchases, grants and balance transfers.",
            examples=["e28e82dc-9df2-4b47-b726-d0a222ef2ab5"],
        ),
    ]
    currency: Annotated[
        Currency,
        Field(
            description="The currency charged for the billing usage entry",
            examples=["USD"],
        ),
    ]
    inferenceDetails: Annotated[
        InferenceDetails,
        Field(description="Details about the related inference request, if applicable"),
    ]
    notes: Annotated[str, Field(description="Notes about the billing usage entry")]
    pricePerUnitUsd: Annotated[float, Field(description="The price per unit in USD")]
    sku: Annotated[str, Field(description="The product associated with the billing usage entry")]
    timestamp: Annotated[
        AwareDatetime,
        Field(
            description="The timestamp the billing usage entry was created (ISO 8601)",
            examples=["2026-06-15T19:05:10.504Z"],
            max_length=40,
        ),
    ]
    units: Annotated[float, Field(description="The number of units consumed")]


class BillingUsageHistoryResponse(VeniceBaseModel):
    data: Annotated[
        list[Datum],
        Field(description="Usage entries in ascending timestamp order", max_length=1000),
    ]
    nextCursor: Annotated[
        str,
        Field(
            description="Continuation token for the next page, to be sent as the cursor query parameter. null means this is the last page.",
            max_length=512,
            pattern="^[A-Za-z0-9_-]+$",
        ),
    ]


class WebScrapeRequest(VeniceBaseModel):
    url: Annotated[AnyUrl, Field(description="The URL to scrape", examples=["https://example.com"])]


class SearchProvider(Enum):
    google = "google"
    brave = "brave"
    exa = "exa"


class WebSearchRequest(VeniceBaseModel):
    query: Annotated[
        str,
        Field(
            description="The search query",
            examples=["latest news about AI"],
            max_length=400,
            min_length=1,
        ),
    ]
    limit: Annotated[
        int | None,
        Field(
            description="Maximum number of results to return (default: 10, max: 20)",
            examples=[10],
            ge=1,
            le=20,
        ),
    ] = 10
    search_provider: Annotated[
        SearchProvider | None,
        Field(
            description='Search provider to use. "brave" uses Brave Search with Zero Data Retention (ZDR) for maximum privacy — search queries are never stored or logged. "google" uses Google Search with anonymized queries — searches are proxied through Venice\'s infrastructure so that your identity is not associated with the search request sent to Google. Venice does not store or log search queries. "exa" uses Exa with Zero Data Retention (ZDR). Defaults to "brave".',
            examples=["brave"],
        ),
    ] = None


class Privacy(Enum):
    private = "private"
    anonymized = "anonymized"


class Deprecation(VeniceBaseModel):
    autoRemap: Annotated[
        bool,
        Field(
            description="When true, Venice may automatically remap API requests for this model ID to replacementModelId instead of returning an error.",
            examples=[False],
        ),
    ]
    date: Annotated[
        str,
        Field(
            description="Legacy ISO 8601 instant aligned with the deprecation sunset used in response headers (`x-venice-model-deprecation-date`). Prefer startsAt / removesAt for new integrations.",
            examples=["2025-03-01T00:00:00.000Z"],
        ),
    ]
    removesAt: Annotated[
        str,
        Field(
            description="ISO 8601 instant when this model ID is omitted from public GET /models listings (same value as `date` today). Consumers should treat the current wall-clock time as past this instant when deciding whether the model remains listed.",
            examples=["2025-04-01T00:00:00.000Z"],
        ),
    ]
    replacementModelId: Annotated[
        str | None,
        Field(
            description="Suggested public API model ID to migrate to, when one exists.",
            examples=["llama-3-3-70b"],
        ),
    ] = None
    startsAt: Annotated[
        str | None,
        Field(
            description="ISO 8601 instant when deprecation warnings and documentation should be considered active for this model.",
            examples=["2025-03-01T00:00:00.000Z"],
        ),
    ] = None


class Quantization(Enum):
    fp4 = "fp4"
    fp8 = "fp8"
    fp16 = "fp16"
    bf16 = "bf16"
    int8 = "int8"
    int4 = "int4"
    not_available = "not-available"


class ReasoningEffortOption(Enum):
    none = "none"
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
    xhigh = "xhigh"
    max = "max"


class DefaultReasoningEffort(Enum):
    none = "none"
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"
    xhigh = "xhigh"
    max = "max"


class Capabilities(VeniceBaseModel):
    optimizedForCode: Annotated[
        bool, Field(description="Is the LLM optimized for coding?", examples=[True])
    ]
    quantization: Annotated[
        Quantization,
        Field(description="The quantization type of the running model.", examples=["fp8"]),
    ]
    supportsFunctionCalling: Annotated[
        bool,
        Field(description="Does the LLM model support function calling?", examples=[True]),
    ]
    supportsAudioInput: Annotated[
        bool, Field(description="Does the LLM support audio input?", examples=[False])
    ]
    supportsReasoning: Annotated[
        bool,
        Field(
            description="Does the model support reasoning with <thinking> blocks of output.",
            examples=[True],
        ),
    ]
    supportsReasoningEffort: Annotated[
        bool,
        Field(
            description="Does the model support the reasoning_effort parameter to control reasoning depth.",
            examples=[True],
        ),
    ]
    reasoningEffortOptions: Annotated[
        list[ReasoningEffortOption] | None,
        Field(
            description='Supported reasoning_effort values for this model. Only present when supportsReasoningEffort is true. The "none" option means reasoning can be disabled.',
            examples=[["none", "low", "medium", "high"]],
        ),
    ] = None
    defaultReasoningEffort: Annotated[
        DefaultReasoningEffort | None,
        Field(
            description="Default reasoning_effort value used when the request does not specify one. Only present when supportsReasoningEffort is true.",
            examples=["medium"],
        ),
    ] = None
    supportsResponseSchema: Annotated[
        bool,
        Field(
            description="Does the LLM model support response schema? Only models that support function calling can support response_schema.",
            examples=[True],
        ),
    ]
    supportsMultipleImages: Annotated[
        bool,
        Field(
            description="Does the LLM support multiple images in a single request? Only applicable when supportsVision is true.",
            examples=[True],
        ),
    ]
    maxImages: Annotated[
        float | None,
        Field(
            description="Maximum number of images supported per request. Only present when supportsMultipleImages is true.",
            examples=[10],
        ),
    ] = None
    maxVideos: Annotated[
        float | None,
        Field(
            description="Maximum number of video attachments supported per chat request. Only present when supportsVideoInput is true.",
            examples=[4],
        ),
    ] = None
    supportsVision: Annotated[
        bool, Field(description="Does the LLM support vision?", examples=[True])
    ]
    supportsVideoInput: Annotated[
        bool, Field(description="Does the LLM support video input?", examples=[True])
    ]
    supportsWebSearch: Annotated[
        bool,
        Field(description="Does the LLM model support web search?", examples=[True]),
    ]
    supportsLogProbs: Annotated[
        bool,
        Field(
            description="Does the LLM model support logprobs parameter?",
            examples=[True],
        ),
    ]
    supportsTeeAttestation: Annotated[
        bool,
        Field(
            description="Does the model run inside a Trusted Execution Environment (TEE) with hardware attestation? When true, use GET /tee/attestation and GET /tee/signature to cryptographically verify that inference occurred inside a genuine TEE.",
            examples=[False],
        ),
    ]
    supportsE2EE: Annotated[
        bool,
        Field(
            description="Does the model support End-to-End Encryption (E2EE)? When true, clients can encrypt prompts using the TEE public key from attestation, and responses are returned encrypted. Requires supportsTeeAttestation to also be true.",
            examples=[False],
        ),
    ]
    supportsXSearch: Annotated[
        bool,
        Field(
            description="Does the model support xAI's native X Search (web + X/Twitter search)? When true, you can use venice_parameters.enable_x_search to activate real-time search powered by xAI.",
            examples=[False],
        ),
    ]


class DefaultQuality(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Steps(VeniceBaseModel):
    default: Annotated[
        float, Field(description="The default steps value for the model", examples=[25])
    ]
    max: Annotated[
        float,
        Field(description="The maximum supported steps value for the model", examples=[50]),
    ]


class Constraints(VeniceBaseModel):
    aspectRatios: Annotated[
        list[str] | None,
        Field(
            description="Supported aspect ratio options for this model. Only present for models that support aspect ratio selection.",
            examples=[[61, 969, 556, 182, 123]],
        ),
    ] = None
    defaultAspectRatio: Annotated[
        str | None,
        Field(
            description="The default aspect ratio for this model. Only present for models that support aspect ratio selection.",
            examples=[61],
        ),
    ] = None
    defaultResolution: Annotated[
        str | None,
        Field(
            description="The default resolution for this model. Only present for models that support resolution selection.",
            examples=["1K"],
        ),
    ] = None
    resolutions: Annotated[
        list[str] | None,
        Field(
            description="Supported resolution options for this model. Only present for models that support resolution selection.",
            examples=[["1K", "2K", "4K"]],
        ),
    ] = None
    defaultQuality: Annotated[
        DefaultQuality | None,
        Field(
            description="The default quality for this model. Only present for models that accept the `quality` request parameter (currently GPT Image 2).",
            examples=["high"],
        ),
    ] = None
    qualities: Annotated[
        list[Quality2] | None,
        Field(
            description="Supported quality options for this model. Only present for models that accept the `quality` request parameter (currently GPT Image 2).",
            examples=[["low", "medium", "high"]],
        ),
    ] = None
    supportsTransparentBackground: Annotated[
        bool | None,
        Field(
            description="Whether this model can return a transparent background (PNG or WebP output only). Only present, as true, for models that support it.",
            examples=[True],
        ),
    ] = None
    promptCharacterLimit: Annotated[
        float,
        Field(description="The maximum supported prompt length.", examples=[2048]),
    ]
    steps: Steps
    widthHeightDivisor: Annotated[
        float,
        Field(
            description="The requested width and height of the image generation must be divisible by this value.",
            examples=[8],
        ),
    ]
    maxStyleReferences: Annotated[
        float | None,
        Field(
            description="Maximum number of style_references accepted by POST /image/generate. Only present for models that support style references.",
            examples=[3],
        ),
    ] = None
    supportsStyleReferenceStrength: Annotated[
        bool | None,
        Field(
            description="Whether per-reference `strength` is honored. When false, style_references strength is ignored. Only present for models that support style references.",
            examples=[True],
        ),
    ] = None


class Temperature(VeniceBaseModel):
    default: Annotated[
        float,
        Field(description="The default temperature value for the model", examples=[0.7]),
    ]


class TopP(VeniceBaseModel):
    default: Annotated[
        float,
        Field(description="The default top_p value for the model", examples=[0.9]),
    ]


class FrequencyPenalty(VeniceBaseModel):
    default: Annotated[
        float,
        Field(
            description="The default frequency_penalty value for the model",
            examples=[0],
        ),
    ]


class PresencePenalty(VeniceBaseModel):
    default: Annotated[
        float,
        Field(description="The default presence_penalty value for the model", examples=[0]),
    ]


class RepetitionPenalty(VeniceBaseModel):
    default: Annotated[
        float,
        Field(
            description="The default repetition_penalty value for the model",
            examples=[1.05],
        ),
    ]


class Constraints1(VeniceBaseModel):
    temperature: Temperature
    top_p: TopP
    frequency_penalty: FrequencyPenalty | None = None
    presence_penalty: PresencePenalty | None = None
    repetition_penalty: RepetitionPenalty | None = None


class ModelType(Enum):
    image_to_video = "image-to-video"
    text_to_video = "text-to-video"
    video = "video"


class Model5(VeniceBaseModel):
    display: str
    value: str


class Slider(VeniceBaseModel):
    default: float
    max: float
    min: float
    param: str
    only_for_models: Annotated[
        list[str] | None,
        Field(description="When present, the parameter only applies to these enhancement models."),
    ] = None


class Select(VeniceBaseModel):
    default: str
    options: list[str]
    param: str


class Topaz(VeniceBaseModel):
    models: Annotated[
        list[Model5] | None,
        Field(description="Available values for the `enhancement_model` request parameter."),
    ] = None
    sliders: Annotated[
        list[Slider] | None,
        Field(description="Numeric enhancement parameters with their valid ranges and defaults."),
    ] = None
    no_upscale_models: Annotated[
        list[str] | None,
        Field(
            description="Enhancement models that must run at source resolution (upscale_factor > 1 is rejected with them)."
        ),
    ] = None
    selects: Annotated[
        list[Select] | None,
        Field(
            description="Enum-style enhancement parameters (e.g. `target_fps`, `output_format`, `slowdown_factor`)."
        ),
    ] = None
    h264_output: Annotated[
        bool | None,
        Field(description="Whether the model accepts the `h264_output` parameter."),
    ] = None
    prompt: Annotated[
        bool | None,
        Field(
            description="Whether the model accepts an optional guidance `prompt` (e.g. Topaz Astra)."
        ),
    ] = None


class Constraints2(VeniceBaseModel):
    aspect_ratios: Annotated[
        list[str],
        Field(
            description="The aspect ratios supported by the model. Empty array means the model does not support a defined aspect ratio.",
            examples=[[969, 556]],
        ),
    ]
    resolutions: Annotated[
        list[str],
        Field(
            description="The resolutions supported by the model. Empty array means the model does not support a defined resolution.",
            examples=[["1080p", "720p", "480p"]],
        ),
    ]
    durations: Annotated[
        list[str],
        Field(
            description="The durations supported by the model. Empty array means the model does not support a defined duration.",
            examples=[["5s", "10s", "15s", "20s", "30s"]],
        ),
    ]
    model_type: Annotated[
        ModelType,
        Field(description="The type of video model.", examples=["image-to-video"]),
    ]
    audio: Annotated[
        bool,
        Field(description="Does the model support audio generation?", examples=[True]),
    ]
    audio_configurable: Annotated[
        bool,
        Field(
            description="Can audio be enabled or disabled for the video generation?",
            examples=[True],
        ),
    ]
    prompt_character_limit: Annotated[
        float | None,
        Field(
            description="The maximum supported prompt length for this video model. If not specified, the default is 2500 characters.",
            examples=[1000],
        ),
    ] = None
    topaz: Annotated[
        Topaz | None,
        Field(
            description="Topaz enhancement controls supported by this model. Absent for regular generation models."
        ),
    ] = None


class Constraints3(VeniceBaseModel):
    aspectRatios: Annotated[
        list[str],
        Field(
            description="The aspect ratios supported by this model. Omit the parameter to use the model's default setting.",
            examples=[["auto", 61, 969, 556]],
        ),
    ]
    promptCharacterLimit: Annotated[
        float,
        Field(description="The maximum supported prompt length.", examples=[1500]),
    ]
    combineImages: Annotated[
        bool,
        Field(
            description="Whether this model supports combining multiple input images.",
            examples=[True],
        ),
    ]
    maxInputImages: Annotated[
        int | None,
        Field(
            description="Maximum number of input images accepted for combine/multi-edit. Absent means the default of 3 (or 1 when combineImages is false).",
            examples=[14],
            gt=0,
        ),
    ] = None
    singleImageAspectRatio: Annotated[
        bool | None,
        Field(
            description="If false, output dimensions match the input on single-image edits and `aspect_ratio` is ignored. Multi-image edits are unaffected. Defaults to true.",
            examples=[True],
        ),
    ] = None
    defaultResolution: Annotated[
        str | None,
        Field(
            description="The default resolution for this inpaint model. Only present for models that support resolution selection (e.g. GPT Image 2 Edit).",
            examples=["1K"],
        ),
    ] = None
    resolutions: Annotated[
        list[str] | None,
        Field(
            description="Supported resolution options for this inpaint model. Only present for models that support resolution selection.",
            examples=[["1K", "2K", "4K"]],
        ),
    ] = None
    defaultQuality: Annotated[
        DefaultQuality | None,
        Field(
            description="The default quality for this inpaint model. Only present for models that accept the `quality` request parameter (currently GPT Image 2 Edit).",
            examples=["high"],
        ),
    ] = None
    qualities: Annotated[
        list[Quality2] | None,
        Field(
            description="Supported quality options for this inpaint model. Only present for models that accept the `quality` request parameter (currently GPT Image 2 Edit).",
            examples=[["low", "medium", "high"]],
        ),
    ] = None
    supportsTransparentBackground: Annotated[
        bool | None,
        Field(
            description="Whether this inpaint model can return a transparent background (PNG or WebP output only). Only present, as true, for models that support it.",
            examples=[True],
        ),
    ] = None


class Input14(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost per million input tokens", examples=[0.7])]
    diem: Annotated[float, Field(description="Diem cost per million input tokens", examples=[7])]


class CacheInput(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per million cached input tokens (discounted rate for cache reads)",
            examples=[0.35],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per million cached input tokens (discounted rate for cache reads)",
            examples=[3.5],
        ),
    ]


class CacheWrite(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per million cache creation tokens (cache writes). For some providers this may be higher than input price.",
            examples=[7.5],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per million cache creation tokens (cache writes). For some providers this may be higher than input price.",
            examples=[75],
        ),
    ]


class Output6(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost per million output tokens", examples=[2.8])]
    diem: Annotated[float, Field(description="Diem cost per million output tokens", examples=[28])]


class Input15(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per million input tokens (extended tier)",
            examples=[11],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per million input tokens (extended tier)",
            examples=[11],
        ),
    ]


class Output7(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per million output tokens (extended tier)",
            examples=[41.25],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per million output tokens (extended tier)",
            examples=[41.25],
        ),
    ]


class CacheInput1(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per million cached input tokens (extended tier)",
            examples=[1.1],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per million cached input tokens (extended tier)",
            examples=[1.1],
        ),
    ]


class CacheWrite1(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per million cache write tokens (extended tier)",
            examples=[13.75],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per million cache write tokens (extended tier)",
            examples=[13.75],
        ),
    ]


class Extended(VeniceBaseModel):
    context_token_threshold: Annotated[
        float,
        Field(
            description="Input token count above which extended pricing applies",
            examples=[200000],
        ),
    ]
    input: Input15
    output: Output7
    cache_input: CacheInput1 | None = None
    cache_write: CacheWrite1 | None = None


class Pricing(VeniceBaseModel):
    input: Input14
    cache_input: Annotated[
        CacheInput | None,
        Field(
            description="Optional pricing for cached input tokens (cache reads). Only present for models that support context caching."
        ),
    ] = None
    cache_write: Annotated[
        CacheWrite | None,
        Field(
            description="Optional pricing for cache creation tokens (cache writes). Only present for models where provider charges for cache writes (e.g., Anthropic charges 1.25x input price)."
        ),
    ] = None
    output: Output6
    extended: Annotated[
        Extended | None,
        Field(
            description="Extended pricing for long-context requests exceeding the threshold. When input tokens exceed context_token_threshold, extended rates apply to the entire request."
        ),
    ] = None


class Generation(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(description="USD cost per image generation (base price)", examples=[0.01]),
    ]
    diem: Annotated[
        float,
        Field(description="Diem cost per image generation (base price)", examples=[0.1]),
    ]


class Resolutions(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for this resolution", examples=[0.18])]
    diem: Annotated[float, Field(description="Diem cost for this resolution", examples=[0.18])]


class Low(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for this resolution", examples=[0.18])]
    diem: Annotated[float, Field(description="Diem cost for this resolution", examples=[0.18])]


class Medium(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for this resolution", examples=[0.18])]
    diem: Annotated[float, Field(description="Diem cost for this resolution", examples=[0.18])]


class High(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for this resolution", examples=[0.18])]
    diem: Annotated[float, Field(description="Diem cost for this resolution", examples=[0.18])]


class Quality6(VeniceBaseModel):
    low: Low | None = None
    medium: Medium | None = None
    high: High | None = None


class Field2x(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for 2x upscale", examples=[0.02])]
    diem: Annotated[float, Field(description="Diem cost for 2x upscale", examples=[0.2])]


class Field4x(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for 4x upscale", examples=[0.08])]
    diem: Annotated[float, Field(description="Diem cost for 4x upscale", examples=[0.8])]


class Upscale(VeniceBaseModel):
    field_2x: Annotated[Field2x, Field(alias="2x")]
    field_4x: Annotated[Field4x, Field(alias="4x")]


class Pricing1(VeniceBaseModel):
    generation: Annotated[
        Generation | None,
        Field(
            description="Base pricing for image generation. Only present for models without resolution-specific pricing."
        ),
    ] = None
    resolutions: Annotated[
        dict[str, Resolutions] | None,
        Field(
            description='Resolution-specific pricing. Keys are resolution tiers (e.g. "1K", "2K", "4K"). Only present for models that support resolution selection. When present, replaces `generation`.',
            examples=[
                {
                    "1K": {"usd": 0.18, "diem": 0.18},
                    "2K": {"usd": 0.24, "diem": 0.24},
                    "4K": {"usd": 0.35, "diem": 0.35},
                }
            ],
        ),
    ] = None
    quality: Annotated[
        dict[str, Quality6] | None,
        Field(
            description="Per-(resolution, quality) pricing. Only present for models that accept the `quality` request parameter (currently GPT Image 2 / GPT Image 2 Edit).",
            examples=[
                {
                    "1K": {
                        "high": {"usd": 0.27, "diem": 0.27},
                        "low": {"usd": 0.02, "diem": 0.02},
                        "medium": {"usd": 0.07, "diem": 0.07},
                    },
                    "2K": {
                        "high": {"usd": 0.5, "diem": 0.5},
                        "low": {"usd": 0.03, "diem": 0.03},
                        "medium": {"usd": 0.13, "diem": 0.13},
                    },
                    "4K": {
                        "high": {"usd": 0.83, "diem": 0.83},
                        "low": {"usd": 0.05, "diem": 0.05},
                        "medium": {"usd": 0.21, "diem": 0.21},
                    },
                }
            ],
        ),
    ] = None
    upscale: Upscale


class Input16(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(description="USD cost per million input characters", examples=[3.5]),
    ]
    diem: Annotated[
        float,
        Field(description="Diem cost per million input characters", examples=[35]),
    ]


class Pricing2(VeniceBaseModel):
    input: Input16


class PerAudioSecond(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost per audio second", examples=[0.0001])]
    diem: Annotated[float, Field(description="Diem cost per audio second", examples=[0.0001])]


class Pricing3(VeniceBaseModel):
    per_audio_second: PerAudioSecond


class Inpaint(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(description="USD cost per image edit/inpaint operation", examples=[0.04]),
    ]
    diem: Annotated[
        float,
        Field(description="Diem cost per image edit/inpaint operation", examples=[0.04]),
    ]


class Additional(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(
            description="USD cost per additional input image beyond the included count",
            examples=[0.0045],
        ),
    ]
    diem: Annotated[
        float,
        Field(
            description="Diem cost per additional input image beyond the included count",
            examples=[0.0045],
        ),
    ]


class InputImages(VeniceBaseModel):
    included: Annotated[
        float,
        Field(
            description='Number of input images included in the base price. Each additional input image adds the "additional" cost.',
            examples=[1],
        ),
    ]
    additional: Additional


class Quality7(VeniceBaseModel):
    low: Low | None = None
    medium: Medium | None = None
    high: High | None = None


class Pricing4(VeniceBaseModel):
    inpaint: Inpaint
    resolutions: Annotated[
        dict[str, Resolutions] | None,
        Field(
            description='Resolution-specific pricing. Keys are resolution tiers (e.g. "1K", "2K", "4K"). Only present for inpaint models that support resolution selection.',
            examples=[
                {
                    "1K": {"usd": 0.36, "diem": 0.36},
                    "2K": {"usd": 0.53, "diem": 0.53},
                    "4K": {"usd": 0.85, "diem": 0.85},
                }
            ],
        ),
    ] = None
    inputImages: Annotated[
        InputImages | None,
        Field(
            description='Input-image pricing. The base price covers "included" input images; each additional input image adds the "additional" cost per output image.'
        ),
    ] = None
    quality: Annotated[
        dict[str, Quality7] | None,
        Field(
            description="Per-(resolution, quality) pricing. Only present for models that accept the `quality` request parameter (currently GPT Image 2 / GPT Image 2 Edit).",
            examples=[
                {
                    "1K": {
                        "high": {"usd": 0.27, "diem": 0.27},
                        "low": {"usd": 0.02, "diem": 0.02},
                        "medium": {"usd": 0.07, "diem": 0.07},
                    },
                    "2K": {
                        "high": {"usd": 0.5, "diem": 0.5},
                        "low": {"usd": 0.03, "diem": 0.03},
                        "medium": {"usd": 0.13, "diem": 0.13},
                    },
                    "4K": {
                        "high": {"usd": 0.83, "diem": 0.83},
                        "low": {"usd": 0.05, "diem": 0.05},
                        "medium": {"usd": 0.21, "diem": 0.21},
                    },
                }
            ],
        ),
    ] = None


class Generation1(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost per music generation", examples=[0.02])]
    diem: Annotated[float, Field(description="Diem cost per music generation", examples=[0.02])]


class Pricing5(VeniceBaseModel):
    generation: Generation1


class Durations(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost for this duration tier", examples=[0.87])]
    diem: Annotated[float, Field(description="Diem cost for this duration tier", examples=[0.87])]
    min_seconds: Annotated[
        float,
        Field(
            description="Minimum duration (inclusive) in seconds that falls into this pricing tier",
            examples=[1],
        ),
    ]
    max_seconds: Annotated[
        float,
        Field(
            description="Maximum duration (inclusive) in seconds that falls into this pricing tier",
            examples=[60],
        ),
    ]


class Pricing6(VeniceBaseModel):
    durations: dict[str, Durations]


class PerSecond(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(description="USD cost per second of generated music", examples=[0.005]),
    ]
    diem: Annotated[
        float,
        Field(description="Diem cost per second of generated music", examples=[0.005]),
    ]


class Pricing7(VeniceBaseModel):
    per_second: PerSecond


class PerThousandCharacters(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost per thousand characters", examples=[0.01])]
    diem: Annotated[float, Field(description="Diem cost per thousand characters", examples=[0.01])]


class Pricing8(VeniceBaseModel):
    per_thousand_characters: PerThousandCharacters


class Mode(Enum):
    zero_shot = "zero_shot"
    persistent = "persistent"


class VoiceCloning(VeniceBaseModel):
    mode: Annotated[
        Mode,
        Field(
            description="How the upstream provider implements voice cloning. `zero_shot` re-reads the reference audio on every synthesis call and never derives a persistent voice template (e.g. Chatterbox HD). `persistent` derives a custom voice template upstream that survives across synthesis calls (e.g. MiniMax Speech-02 HD).",
            examples=["zero_shot"],
        ),
    ]
    accepted_formats: Annotated[
        list[str],
        Field(
            description="Audio container formats this model accepts as a reference sample on POST /v1/audio/voices. Samples in other containers are rejected with HTTP 400 before any upload.",
            examples=[["mp3", "wav", "flac", "mp4"]],
        ),
    ]
    min_sample_seconds: Annotated[
        float,
        Field(
            description="Recommended minimum length of the reference audio sample, in seconds, for an intelligible clone.",
            examples=[5],
        ),
    ]
    retention_days: Annotated[
        float,
        Field(
            description="Days a `vv_<id>` voice handle remains valid against this model. For `persistent` models the upstream provider auto-deletes the cloned voice after this many days without use; each successful TTS request resets the window. For `zero_shot` models this is the storage TTL on the uploaded reference audio; the handle stops working when it expires and the user must re-upload.",
            examples=[7],
        ),
    ]


class ModelSpec(VeniceBaseModel):
    availableContextTokens: Annotated[
        float | None,
        Field(
            description="The context length supported by the model. Only applicable for text models.",
            examples=[1000000],
        ),
    ] = None
    maxCompletionTokens: Annotated[
        float | None,
        Field(
            description="The maximum number of completion tokens the model can generate. Use this to know the upper bound for the max_completion_tokens request parameter. Only applicable for text models.",
            examples=[65536],
        ),
    ] = None
    beta: Annotated[
        bool | None,
        Field(
            description="Is this model restricted to beta users only? If true, only users with beta access can use this model",
            examples=[False],
        ),
    ] = None
    betaModel: Annotated[
        bool | None,
        Field(description="Is this model in beta status?", examples=[False]),
    ] = None
    privacy: Annotated[
        Privacy,
        Field(
            description="The privacy mode of the model. Private models have zero data retention. Anonymized models Venice can not guarantee privacy on, but requests are not affiliated with a user",
            examples=["private"],
        ),
    ]
    regionRestrictions: Annotated[
        list[str] | None,
        Field(
            description="Country codes where this model is intended to be available. Only present for models with region restrictions metadata.",
            examples=[["US"]],
        ),
    ] = None
    deprecation: Annotated[
        Deprecation | None,
        Field(
            description="Deprecation information for the model. Only present for models scheduled to be retired",
            examples=[
                {
                    "autoRemap": False,
                    "date": "2025-03-01T00:00:00.000Z",
                    "removesAt": "2025-03-01T00:00:00.000Z",
                }
            ],
        ),
    ] = None
    capabilities: Annotated[
        Capabilities | None, Field(description="Text model specific capabilities.")
    ] = None
    constraints: Annotated[
        Constraints | Constraints1 | Constraints2 | Constraints3 | None,
        Field(description="Constraints that apply to this model."),
    ] = None
    supportsStyleReferences: Annotated[
        bool | None,
        Field(
            description="Whether this image model accepts `style_references` on POST /image/generate. Only present for image models.",
            examples=[True],
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description="A human-readable description of the model and its capabilities.",
            examples=[
                "Balanced blend of speed and capability. Handles most everyday tasks with reliability."
            ],
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(description="The name of the model.", examples=["Gemini 4 Argon"]),
    ] = None
    modelSource: Annotated[
        str | None,
        Field(
            description="The source of the model, such as a URL to the model repository.",
            examples=[""],
        ),
    ] = None
    offline: Annotated[
        bool | None,
        Field(description="Is this model presently offline?", examples=[False]),
    ] = False
    pricing: Annotated[
        Pricing
        | Pricing1
        | Pricing2
        | Pricing3
        | Pricing4
        | Pricing5
        | Pricing6
        | Pricing7
        | Pricing8
        | None,
        Field(description="Pricing details for the model"),
    ] = None
    traits: Annotated[
        list[str] | None,
        Field(
            description="Traits that apply to this model. You can specify a trait to auto-select a model vs. specifying the model ID in your request to avoid breakage as Venice updates and iterates on its models.",
            examples=[["default_code"]],
        ),
    ] = None
    uncensored: Annotated[
        bool | None,
        Field(
            description="Present and true when Venice classifies this model as uncensored, meaning it applies minimal content-based filtering. Covers every modality, including the video models listed under the `uncensored` model set. Absent for all other models. Upstream providers may still apply their own filtering.",
            examples=[True],
        ),
    ] = None
    embeddingDimensions: Annotated[
        float | None,
        Field(
            description="The native/default number of dimensions in the output embedding vector. Only present for embedding models.",
            examples=[1024],
        ),
    ] = None
    maxInputTokens: Annotated[
        float | None,
        Field(
            description="Maximum number of input tokens the model accepts per input string. Only present for embedding models.",
            examples=[8192],
        ),
    ] = None
    supportsCustomDimensions: Annotated[
        bool | None,
        Field(
            description="Whether the model supports reducing output dimensions via the `dimensions` request parameter. Only present for embedding models that support it.",
            examples=[True],
        ),
    ] = None
    maxStateTokens: Annotated[
        float | None,
        Field(
            description="Maximum tokens for `state` plus the single longest question. Only present for decision models.",
            examples=[32000],
        ),
    ] = None
    maxTotalTokens: Annotated[
        float | None,
        Field(
            description="Maximum tokens for `state` plus all questions combined. Only present for decision models.",
            examples=[64000],
        ),
    ] = None
    supports_lyrics: Annotated[
        bool | None,
        Field(
            description="Whether this audio-generation model supports lyrics input.",
            examples=[True],
        ),
    ] = None
    lyrics_required: Annotated[
        bool | None,
        Field(
            description="Whether lyrics input is required for this audio-generation model.",
            examples=[False],
        ),
    ] = None
    supports_force_instrumental: Annotated[
        bool | None,
        Field(
            description="Whether this audio-generation model supports the force_instrumental request parameter.",
            examples=[True],
        ),
    ] = None
    supports_loop: Annotated[
        bool | None,
        Field(
            description="Whether this audio-generation model supports the loop request parameter.",
            examples=[True],
        ),
    ] = None
    voices: Annotated[
        list[str] | None,
        Field(
            description="The voices available for this model. Applicable for TTS models and voice-enabled music models. Note: each model has its own set of supported voices.",
            examples=[["Achernar", "Achird", "Aiden", "Alex", "Algenib"]],
        ),
    ] = None
    voice_cloning: Annotated[
        VoiceCloning | None,
        Field(
            description="Voice-cloning capability. Only present for TTS models whose cloning endpoint is available to the caller — pass the model to POST /v1/audio/voices to mint a `vv_<id>` voice handle, then pass that handle back as the `voice` parameter on POST /v1/audio/speech alongside the same `model`.",
            title="TTS Voice Cloning",
        ),
    ] = None
    default_voice: Annotated[
        str | None,
        Field(
            description="Default voice for voice-enabled music models.",
            examples=["Aria"],
        ),
    ] = None
    supports_custom_voice_id: Annotated[
        bool | None,
        Field(
            description="Whether this model accepts a caller-supplied provider Voice ID in the `voice` parameter in addition to its curated `voices` (e.g. paste an ElevenLabs Voice ID).",
            examples=[True],
        ),
    ] = None
    supports_language_code: Annotated[
        bool | None,
        Field(
            description="Whether this music model supports an ISO 639-1 language_code parameter.",
            examples=[True],
        ),
    ] = None
    voice_changer: Annotated[
        bool | None,
        Field(
            description="Whether this model performs speech-to-speech conversion. Present only on voice-changer models, which take a source recording instead of a prompt and are served by the POST /v1/audio/voice-changer/* endpoints rather than POST /v1/audio/queue.",
            examples=[True],
        ),
    ] = None
    supports_background_noise_removal: Annotated[
        bool | None,
        Field(
            description="Whether this voice-changer model accepts the remove_background_noise request parameter.",
            examples=[True],
        ),
    ] = None
    supports_seed: Annotated[
        bool | None,
        Field(
            description="Whether this voice-changer model accepts a seed request parameter for reproducible output.",
            examples=[True],
        ),
    ] = None
    accepted_audio_formats: Annotated[
        list[str] | None,
        Field(
            description="Audio container formats this voice-changer model accepts as a source recording. The verdict comes from the file's binary signature, not its filename or declared content type, so mislabelled uploads in an accepted container still succeed and correctly-labelled uploads in an unaccepted one are rejected with HTTP 400 before any charge.",
            examples=[["mp3", "wav", "ogg", "mp4", "aac"]],
        ),
    ] = None
    max_source_audio_duration_seconds: Annotated[
        float | None,
        Field(
            description="Longest source recording this voice-changer model accepts, in seconds. Voice Changer is billed off the length of the source recording, measured server-side and rounded up to the next whole minute, so this bounds the cost of a single request. Longer recordings are rejected with HTTP 422 before any charge.",
            examples=[300],
        ),
    ] = None
    supports_speed: Annotated[
        bool | None,
        Field(
            description="Whether this music model supports speed adjustment.",
            examples=[True],
        ),
    ] = None
    default_speed: Annotated[
        float | None,
        Field(description="Default speed multiplier for this music model.", examples=[1]),
    ] = None
    min_speed: Annotated[
        float | None,
        Field(
            description="Minimum speed multiplier for this music model.",
            examples=[0.25],
        ),
    ] = None
    max_speed: Annotated[
        float | None,
        Field(description="Maximum speed multiplier for this music model.", examples=[4]),
    ] = None
    duration_options: Annotated[
        list[float] | None,
        Field(
            description="Available duration options in seconds for this music model.",
            examples=[[60, 120, 180, 240]],
        ),
    ] = None
    min_duration: Annotated[
        float | None,
        Field(
            description="Minimum duration in seconds for this music model.",
            examples=[60],
        ),
    ] = None
    max_duration: Annotated[
        float | None,
        Field(
            description="Maximum duration in seconds for this music model.",
            examples=[240],
        ),
    ] = None
    default_duration: Annotated[
        float | None,
        Field(
            description="Default duration in seconds for this music model.",
            examples=[60],
        ),
    ] = None
    supported_formats: Annotated[
        list[str] | None,
        Field(
            description="Supported output audio formats for this TTS or music model. An explicit format outside this list is rejected by the corresponding generation endpoint.",
            examples=[["mp3", "wav"]],
        ),
    ] = None
    default_format: Annotated[
        str | None,
        Field(
            description="Output audio format used when the request omits a format. Applicable to TTS and music models.",
            examples=["mp3"],
        ),
    ] = None
    prompt_character_limit: Annotated[
        float | None,
        Field(
            description="Maximum prompt character limit for this music model.",
            examples=[500],
        ),
    ] = None
    min_prompt_length: Annotated[
        float | None,
        Field(description="Minimum prompt length for this music model.", examples=[1]),
    ] = None
    lyrics_character_limit: Annotated[
        float | None,
        Field(
            description="Maximum lyrics character limit for this music model.",
            examples=[3000],
        ),
    ] = None


class Object1(Enum):
    model = "model"


class OwnedBy(Enum):
    venice_ai = "venice.ai"


class Type99(Enum):
    asr = "asr"
    decision = "decision"
    embedding = "embedding"
    image = "image"
    music = "music"
    text = "text"
    tts = "tts"
    upscale = "upscale"
    inpaint = "inpaint"
    video = "video"


class ModelResponse(VeniceBaseModel):
    context_length: Annotated[
        float | None,
        Field(
            description="The context length (maximum input tokens) supported by the model. Only present for text models. This is a standard OpenAI-compatible field that mirrors model_spec.availableContextTokens for client compatibility.",
            examples=[131072],
        ),
    ] = None
    created: Annotated[
        float | None,
        Field(description="Release date on Venice API", examples=[1699000000]),
    ] = None
    discount_to_user: Annotated[
        float | None,
        Field(
            description="Fractional discount carried by a reseller agreement covering this model, e.g. 0.2 for 20% off, following the OpenRouter convention of publishing a base price alongside a separate discount fraction: user price = base price × (1 - discount_to_user). Returned only to the reselling partner whose agreement it belongs to, and omitted for every other caller and for models no agreement covers, so an integration should treat an absent field as no discount. Always greater than 0 and less than 1. Prices in model_spec.pricing are what Venice bills and already reflect any promotional discount active for the caller, so apply discount_to_user to those published prices rather than to a separate list rate. Callers buying from Venice directly rather than through a reseller should ignore this field.",
            examples=[0.2],
            gt=0.0,
            lt=1.0,
        ),
    ] = None
    id: Annotated[str, Field(description="Model ID", examples=["gemini-4-argon"])]
    model_spec: ModelSpec
    object: Annotated[Object1, Field(description="Object type", examples=["model"])]
    owned_by: Annotated[OwnedBy, Field(description="Who runs the model", examples=["venice.ai"])]
    type: Annotated[Type99, Field(description="Model type", examples=["text"])]


class ModelTraitSchema(RootModel[dict[str, str]]):
    root: dict[str, str]


class ModelCompatibilitySchema(RootModel[dict[str, str]]):
    root: dict[str, str]


class Format6(Enum):
    markdown = "markdown"


class WebScrapeResponse(VeniceBaseModel):
    url: Annotated[
        str,
        Field(description="The URL that was scraped", examples=["https://example.com"]),
    ]
    content: Annotated[str, Field(description="The scraped content in markdown format")]
    format: Annotated[Format6, Field(description="The format of the scraped content")]


class Result(VeniceBaseModel):
    title: Annotated[str, Field(description="The title of the search result")]
    url: Annotated[str, Field(description="The URL of the search result")]
    content: Annotated[str, Field(description="A snippet or description of the search result")]
    date: Annotated[str, Field(description="The date of the search result, if available")]


class WebSearchResponse(VeniceBaseModel):
    query: Annotated[str, Field(description="The search query that was executed")]
    results: Annotated[list[Result], Field(description="The search results")]
