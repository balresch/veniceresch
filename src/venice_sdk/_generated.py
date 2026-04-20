# AUTO-GENERATED from vendor/venice-swagger.yaml. Do not edit by hand.

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Annotated, Any

from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel

from venice_sdk._base_model import VeniceBaseModel


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


class Error(Enum):
    Payment_required = "Payment required"


class Code(Enum):
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"


class TopUpInstructions(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
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
                "Sign a USDC transfer authorization using the x402 SDK (createPaymentHeader)"
            ],
        ),
    ]
    step3: Annotated[
        str,
        Field(
            description="Third step: submit the payment.",
            examples=["POST /api/v1/x402/top-up with the signed X-402-Payment header"],
        ),
    ]
    receiverWallet: Annotated[
        str,
        Field(
            description="Venice receiver wallet address.",
            examples=["<RECEIVER_WALLET_ADDRESS>"],
        ),
    ]
    tokenAddress: Annotated[
        str,
        Field(
            description="USDC token contract address.",
            examples=["<USDC_TOKEN_ADDRESS>"],
        ),
    ]
    tokenDecimals: Annotated[float, Field(description="Token decimal places.", examples=[6])]
    network: Annotated[
        str, Field(description="Target blockchain network.", examples=["eip155:8453"])
    ]
    minimumAmountUsd: Annotated[
        float, Field(description="Minimum top-up amount in USD.", examples=[5])
    ]


class SiwxChallenge(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    domain: Annotated[
        str,
        Field(description="Domain for the SIWX challenge.", examples=["api.venice.ai"]),
    ]
    address: Annotated[
        str,
        Field(
            description="Placeholder for wallet address.",
            examples=["{{walletAddress}}"],
        ),
    ]
    uri: Annotated[
        str,
        Field(
            description="Resource URI for the challenge.",
            examples=["https://api.venice.ai/api/v1/x402/top-up"],
        ),
    ]
    version: Annotated[str, Field(description="SIWX version.", examples=["1"])]
    chainId: Annotated[float, Field(description="Chain ID for the signature.", examples=[8453])]
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
            examples=["Sign in with your wallet to access Venice x402 API"],
        ),
    ]


class X402InferencePaymentRequired(VeniceBaseModel):
    error: Annotated[Error, Field(description="Error message indicating payment is required.")]
    code: Annotated[Code, Field(description="Machine-readable error code.")]
    message: Annotated[
        str | None,
        Field(
            description="Human-readable context about the payment requirement.",
            examples=["Insufficient x402 balance"],
        ),
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
        Field(description="List of supported blockchain networks.", examples=[["base"]]),
    ]
    topUpInstructions: TopUpInstructions
    siwxChallenge: SiwxChallenge


class Type(Enum):
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
        Type,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type1(Enum):
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
    type: Annotated[Type1, Field(title="Text Content String")]


class Type2(Enum):
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
        Type2,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class ImageUrl(VeniceBaseModel):
    url: Annotated[
        AnyUrl,
        Field(
            description="The URL of the image. Can be a data URL with a base64 encoded image or a public URL. URL must be publicly accessible. Image must pass validation checks and be >= 64 pixels square."
        ),
    ]


class Type3(Enum):
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
    type: Type3


class Type4(Enum):
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
        Type4,
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


class Type5(Enum):
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
    type: Type5


class Type6(Enum):
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
        Type6,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type7(Enum):
    video_url = "video_url"


class VideoUrl(VeniceBaseModel):
    url: Annotated[
        AnyUrl,
        Field(
            description="The URL of the video. Can be a direct URL (including YouTube links for some providers), or a base64-encoded data URL (e.g., data:video/mp4;base64,...). Supported formats: mp4, mpeg, mov, webm."
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
    type: Type7
    video_url: Annotated[
        VideoUrl,
        Field(
            description="Object containing the video URL information",
            title="Video URL Object",
        ),
    ]


class Role(Enum):
    user = "user"


class Messages(VeniceBaseModel):
    content: str | list[Content | Content1 | Content2 | Content3]
    name: str | None = None
    role: Role


class Type8(Enum):
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
        Type8,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type9(Enum):
    text = "text"


class ContentItem(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl4 | None,
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
    type: Annotated[Type9, Field(title="Text Content String")]


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
    tool_calls: list[Any] | None = None


class Role2(Enum):
    tool = "tool"


class Messages2(VeniceBaseModel):
    content: str
    name: str | None = None
    reasoning_content: str | None = None
    role: Role2
    tool_call_id: str
    tool_calls: list[Any] | None = None


class Type10(Enum):
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
        Type10,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type11(Enum):
    text = "text"


class ContentItem1(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl5 | None,
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
    type: Annotated[Type11, Field(title="Text Content String")]


class Role3(Enum):
    system = "system"


class Messages3(VeniceBaseModel):
    content: str | list[ContentItem1]
    name: str | None = None
    role: Role3


class Type12(Enum):
    ephemeral = "ephemeral"


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


class Type13(Enum):
    text = "text"


class ContentItem2(VeniceBaseModel):
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
    type: Annotated[Type13, Field(title="Text Content String")]


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
            description="On supported reasoning models, will disable thinking and strip the <think></think> blocks from the response. Defaults to false.",
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


class Type14(Enum):
    json_schema = "json_schema"


class ResponseFormat(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    json_schema: dict[str, Any]
    type: Type14


class Type15(Enum):
    json_object = "json_object"


class ResponseFormat1(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    type: Type15


class Type16(Enum):
    text = "text"


class ResponseFormat2(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    type: Type16


class Function(VeniceBaseModel):
    name: str


class ToolChoice(VeniceBaseModel):
    function: Function
    type: str


class Type17(Enum):
    web_search = "web_search"
    x_search = "x_search"


class Tools(VeniceBaseModel):
    type: Type17


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
    model_config = ConfigDict(
        extra="forbid",
    )
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
            examples=["zai-org-glm-4.7"],
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
            description="OpenAI-compatible parameter to control reasoning effort level for supported models. Takes precedence over reasoning.effort if both are provided.",
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
            description="This field is discarded on the request but is supported in the Venice API for compatibility with OpenAI clients."
        ),
    ] = None
    store: Annotated[
        bool | None,
        Field(
            description="This field is accepted for OpenAI compatibility but is not used by Venice."
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


class Type18(Enum):
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
        Type18,
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


class Type19(Enum):
    input_audio = "input_audio"


class ChatCompletionContentPartInputAudio(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl7 | None,
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
    type: Type19


class Type20(Enum):
    ephemeral = "ephemeral"


class CacheControl8(VeniceBaseModel):
    ttl: Annotated[
        str | None,
        Field(
            description="Optional TTL for extended cache duration. Beta feature requiring special header.",
            examples=["1h"],
        ),
    ] = None
    type: Annotated[
        Type20,
        Field(
            description='The type of cache control. Currently only "ephemeral" is supported.',
            examples=["ephemeral"],
        ),
    ]


class Type21(Enum):
    video_url = "video_url"


class ChatCompletionContentPartVideoUrl(VeniceBaseModel):
    cache_control: Annotated[
        CacheControl8 | None,
        Field(
            description="Optional cache control for prompt caching on supported providers.",
            examples=[{"type": "ephemeral"}],
            title="Cache Control",
        ),
    ] = None
    type: Type21
    video_url: Annotated[
        VideoUrl,
        Field(
            description="Object containing the video URL information",
            title="Video URL Object",
        ),
    ]


class Type22(Enum):
    message = "message"


class Role5(Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    developer = "developer"


class Type23(Enum):
    input_text = "input_text"


class Content4(VeniceBaseModel):
    type: Type23
    text: str


class Type24(Enum):
    input_image = "input_image"


class Detail(Enum):
    auto = "auto"
    low = "low"
    high = "high"


class ImageUrl1(VeniceBaseModel):
    url: str
    detail: Detail | None = None


class Content5(VeniceBaseModel):
    type: Type24
    image_url: ImageUrl1


class Type25(Enum):
    output_text = "output_text"


class Content6(VeniceBaseModel):
    type: Type25
    text: str
    annotations: list[Any] | None = None


class Status(Enum):
    completed = "completed"
    in_progress = "in_progress"


class Input(VeniceBaseModel):
    type: Type22
    role: Role5
    content: str | list[Content4 | Content5 | Content6]
    id: str | None = None
    status: Status | None = None


class Type26(Enum):
    input_text = "input_text"


class Content7(VeniceBaseModel):
    type: Type26
    text: str


class Type27(Enum):
    input_image = "input_image"


class ImageUrl2(VeniceBaseModel):
    url: str
    detail: Detail | None = None


class Content8(VeniceBaseModel):
    type: Type27
    image_url: ImageUrl2


class Type28(Enum):
    output_text = "output_text"


class Content9(VeniceBaseModel):
    type: Type28
    text: str
    annotations: list[Any] | None = None


class Type29(Enum):
    text = "text"


class Content10(VeniceBaseModel):
    type: Type29
    text: str


class Type30(Enum):
    image_url = "image_url"


class ImageUrl3(VeniceBaseModel):
    url: str
    detail: Detail | None = None


class Content11(VeniceBaseModel):
    type: Type30
    image_url: str | ImageUrl3


class Input1(VeniceBaseModel):
    role: Role5
    content: str | list[Content7 | Content8 | Content9 | Content10 | Content11]
    id: str | None = None
    status: Status | None = None


class Type31(Enum):
    reasoning = "reasoning"


class Input2(VeniceBaseModel):
    type: Type31
    id: str | None = None
    summary: list[str] | None = None
    content: str | list[Any] | Any | None = None
    encrypted_content: str | None = None
    status: Status | None = None


class Type32(Enum):
    function_call = "function_call"


class Input3(VeniceBaseModel):
    type: Type32
    id: str | None = None
    call_id: str
    name: str
    arguments: str
    status: Status | None = None


class Type33(Enum):
    function_call_output = "function_call_output"


class Input4(VeniceBaseModel):
    type: Type33
    call_id: str
    output: str | list[Any] | dict[str, Any] | float | bool | Any


class Type34(Enum):
    item_reference = "item_reference"


class Input5(VeniceBaseModel):
    type: Type34
    id: str


class Reasoning1(VeniceBaseModel):
    effort: Annotated[
        Effort | None,
        Field(description="Controls reasoning effort level for supported models."),
    ] = None
    summary: Annotated[Summary | None, Field(description="Controls reasoning summary format.")] = (
        None
    )


class Type35(Enum):
    function = "function"


class Function2(VeniceBaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    strict: bool | None = None


class Tools2(VeniceBaseModel):
    type: Type35
    function: Function2


class Type36(Enum):
    web_search = "web_search"


class SearchContextSize(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Type37(Enum):
    approximate = "approximate"


class UserLocation(VeniceBaseModel):
    type: Type37 | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    timezone: str | None = None


class Tools3(VeniceBaseModel):
    type: Type36
    search_context_size: SearchContextSize | None = None
    user_location: UserLocation | None = None


class Type38(Enum):
    x_search = "x_search"


class Tools4(VeniceBaseModel):
    type: Type38
    allowed_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    excluded_x_handles: Annotated[list[str] | None, Field(max_length=10)] = None
    from_date: str | None = None
    to_date: str | None = None
    enable_image_understanding: bool | None = None
    enable_video_understanding: bool | None = None


class Type39(Enum):
    code_interpreter = "code_interpreter"


class Container(VeniceBaseModel):
    image: str | None = None


class Tools5(VeniceBaseModel):
    type: Type39
    container: Container | None = None


class Type40(Enum):
    file_search = "file_search"


class RankingOptions(VeniceBaseModel):
    ranker: str | None = None
    score_threshold: float | None = None


class Tools6(VeniceBaseModel):
    type: Type40
    vector_store_ids: list[str] | None = None
    max_num_results: int | None = None
    ranking_options: RankingOptions | None = None


class Type41(Enum):
    computer_use_preview = "computer_use_preview"


class Tools7(VeniceBaseModel):
    type: Type41
    display_width: int | None = None
    display_height: int | None = None
    environment: str | None = None


class Tools8(VeniceBaseModel):
    type: str


class ToolChoice1(Enum):
    auto = "auto"


class ToolChoice2(Enum):
    none = "none"


class ToolChoice3(Enum):
    required = "required"


class Type42(Enum):
    function = "function"


class Function3(VeniceBaseModel):
    name: str


class ToolChoice4(VeniceBaseModel):
    type: Type42
    function: Function3


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
            examples=["zai-org-glm-5"],
        ),
    ]
    input: Annotated[
        str | list[Input | Input1 | Input2 | Input3 | Input4 | Input5],
        Field(
            description="The input to generate a response for. Can be a simple string or an array of messages."
        ),
    ]
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
    reasoning: Annotated[Reasoning1 | None, Field(title="Reasoning Configuration")] = None
    tools: Annotated[
        list[Tools2 | Tools3 | Tools4 | Tools5 | Tools6 | Tools7 | Tools8] | None,
        Field(description="A list of tools the model may call."),
    ] = None
    tool_choice: Annotated[
        ToolChoice1 | ToolChoice2 | ToolChoice3 | ToolChoice4 | None,
        Field(description="Controls which tool is called by the model."),
    ] = None
    web_search: Annotated[bool | None, Field(description="Enable web search for this request.")] = (
        None
    )
    stream: Annotated[
        bool | None, Field(description="Whether to stream back partial progress.")
    ] = None
    venice_parameters: Annotated[VeniceParameters1 | None, Field(title="Venice Parameters")] = None


class Object(Enum):
    response = "response"


class Status4(Enum):
    completed = "completed"
    failed = "failed"
    in_progress = "in_progress"
    cancelled = "cancelled"


class Type43(Enum):
    reasoning = "reasoning"


class Output(VeniceBaseModel):
    type: Type43
    id: str
    summary: list[str] | None = None
    encrypted_content: str | None = None


class Type44(Enum):
    message = "message"


class Status5(Enum):
    completed = "completed"
    in_progress = "in_progress"
    failed = "failed"


class Role7(Enum):
    assistant = "assistant"


class Type45(Enum):
    output_text = "output_text"


class Type46(Enum):
    url_citation = "url_citation"


class Annotation(VeniceBaseModel):
    type: Type46
    url: str
    title: str | None = None
    start_index: int
    end_index: int


class ContentItem3(VeniceBaseModel):
    type: Type45
    text: str
    annotations: list[Annotation] | None = None


class Output1(VeniceBaseModel):
    type: Type44
    id: str
    status: Status5
    role: Role7
    content: list[ContentItem3]


class Type47(Enum):
    function_call = "function_call"


class Status6(Enum):
    completed = "completed"
    in_progress = "in_progress"


class Output2(VeniceBaseModel):
    type: Type47
    id: str
    call_id: str
    name: str
    arguments: str
    status: Status6


class Type48(Enum):
    web_search_call = "web_search_call"


class Status7(Enum):
    completed = "completed"


class Output3(VeniceBaseModel):
    type: Type48
    id: str
    status: Status7


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


class Error1(VeniceBaseModel):
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
    status: Annotated[Status4, Field(description="The status of the response.")]
    output: Annotated[
        list[Output | Output1 | Output2 | Output3],
        Field(description="The output items generated by the model."),
    ]
    usage: Annotated[Usage | None, Field(description="Token usage statistics.", title="Usage")] = (
        None
    )
    error: Annotated[
        Error1 | None,
        Field(description="Error information if the response failed.", title="Error"),
    ] = None


class Format2(Enum):
    jpeg = "jpeg"
    png = "png"
    webp = "webp"


class GenerateImageRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
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
        Format2 | None,
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
            examples=["z-image-turbo"],
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
            description="Number of images to generate (1–4). Only supported when return_binary is false.",
            examples=[3],
            ge=1,
            le=4,
        ),
    ] = None
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to use safe mode. If enabled, this will blur images that are classified as having adult content.",
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
    enable_web_search: Annotated[
        bool | None,
        Field(
            description="Enable web search for the image generation task. This will allow the model to use the latest information from the web to generate the image. Only supported by certain models. If web search is used, additional credits are getting charged.",
            examples=[False],
        ),
    ] = None
    width: Annotated[
        int | None,
        Field(description="Width of the generated image.", examples=[1024], gt=0, le=1280),
    ] = 1024


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


class Quality(Enum):
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
    model_config = ConfigDict(
        extra="forbid",
    )
    background: Annotated[
        Background | None,
        Field(
            description="This parameter is not used in Venice image generation but is supported for compatibility with OpenAI API",
            examples=["auto"],
        ),
    ] = "auto"
    model: Annotated[
        str | None,
        Field(
            description="The model to use for image generation. Defaults to Venice's default image model. If a non-existent model is specified (ie an OpenAI model name), it will default to Venice's default image model.",
            examples=["z-image-turbo"],
        ),
    ] = "default"
    moderation: Annotated[
        Moderation | None,
        Field(
            description="auto enables safe venice mode which will blur out adult content. low disables safe venice mode.",
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
        Quality | None,
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
            description="This parameter is not used in Venice image generation but is supported for compatibility with OpenAI API",
            examples=["user123"],
        ),
    ] = None


class Enhance(Enum):
    true = "true"
    false = "false"


class UpscaleImageRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    enhance: Annotated[
        bool | Enhance | None,
        Field(
            description="Whether to enhance the image using Venice's image engine during upscaling. Must be true if scale is 1.",
            examples=[True],
        ),
    ] = "false"
    enhanceCreativity: Annotated[
        float | None,
        Field(
            description="Higher values let the enhancement AI change the image more. Setting this to 1 effectively creates an entirely new image.",
            examples=[0.5],
            ge=0.0,
            le=1.0,
        ),
    ] = 0.5
    enhancePrompt: Annotated[
        str | None,
        Field(
            description="The text to image style to apply during prompt enhancement. Does best with short descriptive prompts, like gold, marble or angry, menacing.",
            examples=["gold"],
            max_length=1500,
        ),
    ] = None
    image: Annotated[
        Any | str,
        Field(
            description="The image to upscale. Can be either a file upload or a base64-encoded string. Image dimensions must be at least 65536 pixels and final dimensions after scaling must not exceed 16777216 pixels. File size must be less than 25MB."
        ),
    ]
    replication: Annotated[
        float | None,
        Field(
            description='How strongly lines and noise in the base image are preserved. Higher values are noisier but less plastic/AI "generated"/hallucinated. Must be between 0 and 1.',
            examples=[0.35],
            ge=0.0,
            le=1.0,
        ),
    ] = 0.35
    scale: Annotated[
        float | None,
        Field(
            description="The scale factor for upscaling the image. Must be a number between 1 and 4. Scale of 1 requires enhance to be set true and will only run the enhancer. Scale must be > 1 if enhance is false. A scale of 4 with large images will result in the scale being dynamically set to ensure the final image stays within the maximum size limits.",
            examples=[2],
            ge=1.0,
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
    field_245 = 245


class EditImageRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    aspect_ratio: Annotated[
        AspectRatio | None,
        Field(
            description="The aspect ratio for the output image. Omit this parameter to use the model's default setting. Supported values vary by model - check GET /api/v1/models for model-specific options.",
            examples=[969],
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
    ] = "qwen-edit"
    modelId: Annotated[
        str | None,
        Field(
            deprecated=True,
            description='Deprecated: Use "model" instead. The model ID to use for image editing.',
            min_length=1,
        ),
    ] = None
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
            description="Whether to use safe mode. If enabled, this will blur images that are classified as having adult content.",
            examples=[False],
        ),
    ] = True


class MultiEditImageRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    modelId: Annotated[
        str | None,
        Field(description="The model ID to use for multi-edit.", min_length=1),
    ] = "qwen-edit"
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
            description="Array of 1 to 3 images used for multi-editing. The first image is treated as the base image, and the remaining images are used as edit layers/masks. Each image can be a base64-encoded string or a URL starting with http:// or https://. Image dimensions must be at least 65536 pixels and must not exceed 33177600 pixels. File size must be less than 25MB."
        ),
    ]
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to use safe mode. If enabled, this will blur images that are classified as having adult content.",
            examples=[False],
        ),
    ] = True


class MultiEditImageMultipartRequest(VeniceBaseModel):
    modelId: Annotated[
        str | None,
        Field(description="The model ID to use for multi-edit.", min_length=1),
    ] = "qwen-edit"
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
            description="Array of 1 to 3 image files. The first image is treated as the base image, and the remaining images are used as edit layers/masks.",
            max_length=3,
            min_length=1,
        ),
    ]
    safe_mode: Annotated[
        bool | None,
        Field(
            description="Whether to use safe mode. If enabled, this will blur images that are classified as having adult content.",
            examples=[False],
        ),
    ] = True


class BackgroundRemoveImageRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    image: Annotated[
        Any | str | None,
        Field(
            description="The image to remove the background from. Can be either a file upload or a base64-encoded string. File size must be less than 25MB."
        ),
    ] = None
    image_url: Annotated[
        AnyUrl | None,
        Field(
            description="URL of the image to remove the background from.",
            examples=["https://example.com/image.jpg"],
        ),
    ] = None


class EncodingFormat(Enum):
    float = "float"
    base64 = "base64"


class Input6(RootModel[str]):
    root: Annotated[
        str,
        Field(
            description="The string that will be turned into an embedding. Cannot be an empty string.",
            examples=["This is a test."],
            min_length=1,
            title="string",
        ),
    ]


class Input7(RootModel[list[str]]):
    root: Annotated[
        list[str],
        Field(
            description="The array of strings that will be turned into an embedding. Array must be 2048 dimensions or less.",
            examples=[["This is a test."]],
            max_length=2048,
            min_length=1,
            title="array",
        ),
    ]


class Input8Item(RootModel[int]):
    root: Annotated[int, Field(ge=1)]


class Input8(RootModel[list[Input8Item]]):
    root: Annotated[
        list[Input8Item],
        Field(
            description="The array of integers that will be turned into an embedding. Array must be 2048 dimensions or less.",
            examples=[[1212, 318, 257, 1332, 13]],
            max_length=2048,
            min_length=1,
            title="array",
        ),
    ]


class Input9Item(RootModel[list[int]]):
    root: Annotated[list[int], Field(min_length=1)]


class Input9(RootModel[list[Input9Item]]):
    root: Annotated[
        list[Input9Item],
        Field(
            description="The array of arrays containing integers that will be turned into an embedding. Array must be 2048 dimensions or less.",
            examples=[[[1212, 318, 257, 1332, 13]]],
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
    model_config = ConfigDict(
        extra="forbid",
    )
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
        Input6 | Input7 | Input8 | Input9,
        Field(
            description="Input text to embed, encoded as a string or array of tokens. To embed multiple inputs in a single request, pass an array of strings or array of token arrays. The input must not exceed the max input tokens for the model (8192 tokens), cannot be an empty string, and any array must be 2048 dimensions or less.",
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


class Model1(Enum):
    tts_kokoro = "tts-kokoro"
    tts_qwen3_0_6b = "tts-qwen3-0-6b"
    tts_qwen3_1_7b = "tts-qwen3-1-7b"
    tts_xai_v1 = "tts-xai-v1"
    tts_inworld_1_5_max = "tts-inworld-1-5-max"
    tts_chatterbox_hd = "tts-chatterbox-hd"
    tts_orpheus = "tts-orpheus"
    tts_elevenlabs_turbo_v2_5 = "tts-elevenlabs-turbo-v2-5"
    tts_minimax_speech_02_hd = "tts-minimax-speech-02-hd"


class ResponseFormat4(Enum):
    mp3 = "mp3"
    opus = "opus"
    aac = "aac"
    flac = "flac"
    wav = "wav"
    pcm = "pcm"


class Voice(Enum):
    af_alloy = "af_alloy"
    af_aoede = "af_aoede"
    af_bella = "af_bella"
    af_heart = "af_heart"
    af_jadzia = "af_jadzia"
    af_jessica = "af_jessica"
    af_kore = "af_kore"
    af_nicole = "af_nicole"
    af_nova = "af_nova"
    af_river = "af_river"
    af_sarah = "af_sarah"
    af_sky = "af_sky"
    am_adam = "am_adam"
    am_echo = "am_echo"
    am_eric = "am_eric"
    am_fenrir = "am_fenrir"
    am_liam = "am_liam"
    am_michael = "am_michael"
    am_onyx = "am_onyx"
    am_puck = "am_puck"
    am_santa = "am_santa"
    bf_alice = "bf_alice"
    bf_emma = "bf_emma"
    bf_lily = "bf_lily"
    bm_daniel = "bm_daniel"
    bm_fable = "bm_fable"
    bm_george = "bm_george"
    bm_lewis = "bm_lewis"
    zf_xiaobei = "zf_xiaobei"
    zf_xiaoni = "zf_xiaoni"
    zf_xiaoxiao = "zf_xiaoxiao"
    zf_xiaoyi = "zf_xiaoyi"
    zm_yunjian = "zm_yunjian"
    zm_yunxi = "zm_yunxi"
    zm_yunxia = "zm_yunxia"
    zm_yunyang = "zm_yunyang"
    ff_siwis = "ff_siwis"
    hf_alpha = "hf_alpha"
    hf_beta = "hf_beta"
    hm_omega = "hm_omega"
    hm_psi = "hm_psi"
    if_sara = "if_sara"
    im_nicola = "im_nicola"
    jf_alpha = "jf_alpha"
    jf_gongitsune = "jf_gongitsune"
    jf_nezumi = "jf_nezumi"
    jf_tebukuro = "jf_tebukuro"
    jm_kumo = "jm_kumo"
    pf_dora = "pf_dora"
    pm_alex = "pm_alex"
    pm_santa = "pm_santa"
    ef_dora = "ef_dora"
    em_alex = "em_alex"
    em_santa = "em_santa"
    Vivian = "Vivian"
    Serena = "Serena"
    Ono_Anna = "Ono_Anna"
    Sohee = "Sohee"
    Uncle_Fu = "Uncle_Fu"
    Dylan = "Dylan"
    Eric = "Eric"
    Ryan = "Ryan"
    Aiden = "Aiden"
    eve = "eve"
    ara = "ara"
    rex = "rex"
    sal = "sal"
    leo = "leo"
    Craig = "Craig"
    Ashley = "Ashley"
    Olivia = "Olivia"
    Sarah = "Sarah"
    Elizabeth = "Elizabeth"
    Priya = "Priya"
    Alex = "Alex"
    Edward = "Edward"
    Theodore = "Theodore"
    Ronald = "Ronald"
    Mark = "Mark"
    Hades = "Hades"
    Luna = "Luna"
    Pixie = "Pixie"
    Aurora = "Aurora"
    Britney = "Britney"
    Siobhan = "Siobhan"
    Vicky = "Vicky"
    Blade = "Blade"
    Carl = "Carl"
    Cliff = "Cliff"
    Richard = "Richard"
    Rico = "Rico"
    tara = "tara"
    leah = "leah"
    jess = "jess"
    mia = "mia"
    zoe = "zoe"
    dan = "dan"
    zac = "zac"
    Rachel = "Rachel"
    Aria = "Aria"
    Laura = "Laura"
    Charlotte = "Charlotte"
    Alice = "Alice"
    Matilda = "Matilda"
    Jessica = "Jessica"
    Lily = "Lily"
    Roger = "Roger"
    Charlie = "Charlie"
    George = "George"
    Callum = "Callum"
    River = "River"
    Liam = "Liam"
    Will = "Will"
    Chris = "Chris"
    Brian = "Brian"
    Daniel = "Daniel"
    Bill = "Bill"
    WiseWoman = "WiseWoman"
    FriendlyPerson = "FriendlyPerson"
    InspirationalGirl = "InspirationalGirl"
    CalmWoman = "CalmWoman"
    LivelyGirl = "LivelyGirl"
    LovelyGirl = "LovelyGirl"
    SweetGirl = "SweetGirl"
    ExuberantGirl = "ExuberantGirl"
    DeepVoiceMan = "DeepVoiceMan"
    CasualGuy = "CasualGuy"
    PatientMan = "PatientMan"
    YoungKnight = "YoungKnight"
    DeterminedMan = "DeterminedMan"
    ImposingManner = "ImposingManner"
    ElegantMan = "ElegantMan"


class CreateSpeechRequestSchema(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
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
        Model1 | None,
        Field(description="The model ID of a Venice TTS model.", examples=["tts-kokoro"]),
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
        Field(description="The format to audio in.", examples=["mp3"]),
    ] = "mp3"
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
        Voice | None,
        Field(
            description="The voice to use when generating the audio. Voices are model-specific: Kokoro (e.g. af_sky, af_bella, am_adam), Qwen 3 (e.g. Vivian, Serena, Dylan), xAI (eve, ara, rex, sal, leo), Orpheus (tara, leah, jess, leo, dan, mia, zac, zoe), Inworld (Craig, Ashley, ...), Chatterbox (Aurora, Blade, ...), ElevenLabs Turbo (Rachel, Aria, ...), MiniMax (WiseWoman, DeepVoiceMan, ...). Using an incompatible voice returns a 400 error. Call GET /models/{id} to list voices for a specific model.",
            examples=["af_sky"],
        ),
    ] = "af_sky"


class Model2(Enum):
    nvidia_parakeet_tdt_0_6b_v3 = "nvidia/parakeet-tdt-0.6b-v3"
    openai_whisper_large_v3 = "openai/whisper-large-v3"
    fal_ai_wizper = "fal-ai/wizper"
    elevenlabs_scribe_v2 = "elevenlabs/scribe-v2"
    stt_xai_v1 = "stt-xai-v1"


class ResponseFormat5(Enum):
    json = "json"
    text = "text"


class CreateTranscriptionRequestSchema(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    file: Annotated[
        bytes | None,
        Field(
            description="The audio file object (not a base64 string). Supported formats: WAV, WAVE, FLAC, M4A, AAC, MP4, MP3, OGG, WEBM."
        ),
    ] = None
    model: Annotated[
        Model2 | None,
        Field(
            description="The model to use for transcription. See https://docs.venice.ai/models/overview for more information.",
            examples=["nvidia/parakeet-tdt-0.6b-v3"],
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


class Duration(Enum):
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
    field_18s = "18s"
    field_20s = "20s"
    field_25s = "25s"
    field_30s = "30s"
    Auto = "Auto"


class AspectRatio1(Enum):
    field_61 = 61
    field_123 = 123
    field_182 = 182
    field_184 = 184
    field_243 = 243
    field_556 = 556
    field_969 = 969
    field_1269 = 1269


class Resolution(Enum):
    field_256p = "256p"
    field_360p = "360p"
    field_480p = "480p"
    field_540p = "540p"
    field_580p = "580p"
    field_720p = "720p"
    field_1080p = "1080p"
    field_1440p = "1440p"
    field_2160p = "2160p"
    field_4k = "4k"
    field_2x = "2x"
    field_4x = "4x"
    true_1080p = "true_1080p"


class UpscaleFactor(IntEnum):
    integer_1 = 1
    integer_2 = 2
    integer_4 = 4


class Element(VeniceBaseModel):
    frontal_image_url: str | None = None
    reference_image_urls: Annotated[list[str] | None, Field(max_length=3)] = None
    video_url: str | None = None


class QueueVideoRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model to use for video generation.",
            examples=["wan-2-7-text-to-video"],
        ),
    ]
    prompt: Annotated[
        str,
        Field(
            description="The prompt to use for video generation. Required for most models. The maximum length varies by model (default 2500 characters, up to 3500 for some models such as Seedance 2.0).",
            examples=["Commerce being conducted in the city of Venice, Italy."],
            max_length=3500,
            min_length=1,
        ),
    ]
    negative_prompt: Annotated[
        str | None,
        Field(
            description="Optional negative prompt. The maximum length varies by model (default 2500 characters, up to 3500 for some models).",
            examples=["low resolution, error, worst quality, low quality, defects"],
            max_length=3500,
        ),
    ] = None
    duration: Annotated[
        Duration,
        Field(
            description="The duration of the video to generate. Available options vary by model.",
            examples=["5s"],
        ),
    ]
    aspect_ratio: Annotated[
        AspectRatio1 | None,
        Field(
            description="The aspect ratio of the video. Available options vary by model. Some models do not support aspect_ratio.",
            examples=[969],
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
    audio: Annotated[
        bool | None,
        Field(
            description="For models which support audio generation and configuration. Defaults to true.",
            examples=[True],
        ),
    ] = True
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
            description="For models with reference image support, up to 9 images for character/style consistency. Each must be a URL or data URL.",
            examples=[["data:image/png;base64,iVBORw0K..."]],
            max_length=9,
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


class QuoteVideoRequest(VeniceBaseModel):
    model: Annotated[
        str,
        Field(
            description="The model to get a price quote for.",
            examples=["wan-2-7-text-to-video"],
        ),
    ]
    duration: Annotated[
        Duration,
        Field(
            description="The duration of the video. Available options vary by model.",
            examples=["5s"],
        ),
    ]
    aspect_ratio: Annotated[
        AspectRatio1 | None,
        Field(
            description="The aspect ratio. Required for some models with megapixel-rate pricing.",
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
        Field(description="For upscale models only.", examples=[2]),
    ] = 2
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


class CompleteVideoRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model: Annotated[
        str,
        Field(
            description="The ID of the model used for video generation.",
            examples=["video-model-123"],
        ),
    ]
    queue_id: Annotated[
        str,
        Field(
            description="The ID of the video generation request.",
            examples=["123e4567-e89b-12d3-a456-426614174000"],
        ),
    ]


class RetrieveVideoRequest(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model: Annotated[
        str,
        Field(
            description="The ID of the model used for video generation.",
            examples=["video-model-123"],
        ),
    ]
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


class CreateVideoTranscriptionRequestSchema(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    url: Annotated[
        str,
        Field(
            description="YouTube video URL to transcribe.",
            examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        ),
    ]
    response_format: Annotated[
        ResponseFormat5 | None,
        Field(
            description="The format of the transcript output, in one of these options: json, text.",
            examples=["json"],
        ),
    ] = "json"


class TextParserRequest(VeniceBaseModel):
    file: Annotated[
        bytes | None,
        Field(
            description="The document file to parse. Supported formats: PDF, DOCX, XLSX, and plain text files. Maximum size: 25MB."
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
    model_config = ConfigDict(
        extra="forbid",
    )
    model: Annotated[
        str,
        Field(
            description="The model to use for audio generation.",
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
    model_config = ConfigDict(
        extra="forbid",
    )
    model: Annotated[
        str,
        Field(
            description="The model to get a price quote for.",
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
    model_config = ConfigDict(
        extra="forbid",
    )
    model: Annotated[
        str,
        Field(
            description="The ID of the model used for audio generation.",
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
    model_config = ConfigDict(
        extra="forbid",
    )
    model: Annotated[
        str,
        Field(
            description="The ID of the model used for audio generation.",
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


class ConsumptionCurrency(Enum):
    USD = "USD"
    VCU = "VCU"
    DIEM = "DIEM"
    BUNDLED_CREDITS = "BUNDLED_CREDITS"


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
        Field(description="Remaining USD balance. Null if not available.", examples=[25]),
    ]


class BillingBalanceResponse(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
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
            description="The currency that will be used for consumption (DIEM or USD)",
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


class Currency(Enum):
    USD = "USD"
    VCU = "VCU"
    DIEM = "DIEM"
    BUNDLED_CREDITS = "BUNDLED_CREDITS"


class SortOrder(Enum):
    asc = "asc"
    desc = "desc"


class BillingUsageRequest(VeniceBaseModel):
    currency: Annotated[
        Currency | None, Field(description="Filter by currency", examples=["USD"])
    ] = None
    endDate: Annotated[
        AwareDatetime | None,
        Field(
            description="End date for filtering records (ISO 8601)",
            examples=["2024-12-31T23:59:59Z"],
        ),
    ] = None
    limit: Annotated[
        int | None,
        Field(description="Number of items per page", examples=[200], gt=0, le=500),
    ] = 200
    page: Annotated[
        int | None, Field(description="Page number for pagination", examples=[1], gt=0)
    ] = 1
    sortOrder: Annotated[
        SortOrder | None,
        Field(description="Sort order for createdAt field", examples=["desc"]),
    ] = "desc"
    startDate: Annotated[
        AwareDatetime | None,
        Field(
            description="Start date for filtering records (ISO 8601)",
            examples=["2024-01-01T00:00:00Z"],
        ),
    ] = None


class InferenceDetails(VeniceBaseModel):
    completionTokens: Annotated[
        float,
        Field(description="Number of tokens used in the completion. Only present for LLM usage."),
    ]
    inferenceExecutionTime: Annotated[
        float, Field(description="Time taken for inference execution in milliseconds")
    ]
    promptTokens: Annotated[
        float,
        Field(description="Number of tokens requested in the prompt. Only present for LLM usage."),
    ]
    requestId: Annotated[str, Field(description="Unique identifier for the inference request")]


class Datum(VeniceBaseModel):
    amount: Annotated[
        float, Field(description="The total amount charged for the billing usage entry")
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
        str,
        Field(
            description="The timestamp the billing usage entry was created",
            examples=["2025-01-01T00:00:00Z"],
        ),
    ]
    units: Annotated[float, Field(description="The number of units consumed")]


class Pagination(VeniceBaseModel):
    limit: float
    page: float
    total: float
    totalPages: float


class BillingUsageResponse(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    warningMessage: Annotated[
        str | None,
        Field(
            description="A warning message to disambiguate DIEM usage from legacy DIEM (formerly VCU) usage"
        ),
    ] = None
    data: list[Datum]
    pagination: Pagination


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
    modelName: Annotated[
        str, Field(description="Display name of the model", examples=["Llama 3.3 70B"])
    ]
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
    model_config = ConfigDict(
        extra="forbid",
    )
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


class WebScrapeRequest(VeniceBaseModel):
    url: Annotated[AnyUrl, Field(description="The URL to scrape", examples=["https://example.com"])]


class SearchProvider(Enum):
    google = "google"
    brave = "brave"


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
            description='Search provider to use. "brave" uses Brave Search with Zero Data Retention (ZDR) for maximum privacy — search queries are never stored or logged. "google" uses Google Search with anonymized queries — searches are proxied through Venice\'s infrastructure so that your identity is not associated with the search request sent to Google. Venice does not store or log search queries. Defaults to "brave".',
            examples=["brave"],
        ),
    ] = None


class Privacy(Enum):
    private = "private"
    anonymized = "anonymized"


class Deprecation(VeniceBaseModel):
    date: Annotated[
        str,
        Field(
            description="The ISO 8601 date when this model is scheduled to be deprecated",
            examples=["2025-03-01T00:00:00.000Z"],
        ),
    ]


class Quantization(Enum):
    fp4 = "fp4"
    fp8 = "fp8"
    fp16 = "fp16"
    bf16 = "bf16"
    int8 = "int8"
    int4 = "int4"
    not_available = "not-available"


class Capabilities(VeniceBaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
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
            description="Does the model support the reasoning_effort parameter to control reasoning depth (low, medium, high).",
            examples=[True],
        ),
    ]
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
    promptCharacterLimit: Annotated[
        float,
        Field(description="The maximum supported prompt length.", examples=[2048]),
    ]
    resolutions: Annotated[
        list[str] | None,
        Field(
            description="Supported resolution options for this model. Only present for models that support resolution selection.",
            examples=[["1K", "2K", "4K"]],
        ),
    ] = None
    steps: Steps
    widthHeightDivisor: Annotated[
        float,
        Field(
            description="The requested width and height of the image generation must be divisible by this value.",
            examples=[8],
        ),
    ]


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


class Input10(VeniceBaseModel):
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


class Output4(VeniceBaseModel):
    usd: Annotated[float, Field(description="USD cost per million output tokens", examples=[2.8])]
    diem: Annotated[float, Field(description="Diem cost per million output tokens", examples=[28])]


class Input11(VeniceBaseModel):
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


class Output5(VeniceBaseModel):
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
    input: Input11
    output: Output5
    cache_input: CacheInput1 | None = None
    cache_write: CacheWrite1 | None = None


class Pricing(VeniceBaseModel):
    input: Input10
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
    output: Output4
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
            description='Resolution-specific pricing. Keys are resolution names (e.g., "1K", "2K", "4K"). Only present for models that support resolution selection. When present, "generation" pricing will not be included.',
            examples=[
                {
                    "1K": {"usd": 0.18, "diem": 0.18},
                    "2K": {"usd": 0.24, "diem": 0.24},
                    "4K": {"usd": 0.35, "diem": 0.35},
                }
            ],
        ),
    ] = None
    upscale: Upscale


class Input12(VeniceBaseModel):
    usd: Annotated[
        float,
        Field(description="USD cost per million input characters", examples=[3.5]),
    ]
    diem: Annotated[
        float,
        Field(description="Diem cost per million input characters", examples=[35]),
    ]


class Pricing2(VeniceBaseModel):
    input: Input12


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


class Pricing4(VeniceBaseModel):
    inpaint: Inpaint


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


class ModelSpec(VeniceBaseModel):
    availableContextTokens: Annotated[
        float | None,
        Field(
            description="The context length supported by the model. Only applicable for text models.",
            examples=[200000],
        ),
    ] = None
    maxCompletionTokens: Annotated[
        float | None,
        Field(
            description="The maximum number of completion tokens the model can generate. Use this to know the upper bound for the max_completion_tokens request parameter. Only applicable for text models.",
            examples=[24000],
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
            description="Deprecation information for the model. Only present for models scheduled to be retired"
        ),
    ] = None
    capabilities: Annotated[
        Capabilities | None, Field(description="Text model specific capabilities.")
    ] = None
    constraints: Annotated[
        Constraints | Constraints1 | Constraints2 | Constraints3 | None,
        Field(description="Constraints that apply to this model."),
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
        str | None, Field(description="The name of the model.", examples=["GLM 5.1"])
    ] = None
    modelSource: Annotated[
        str | None,
        Field(
            description="The source of the model, such as a URL to the model repository.",
            examples=["https://huggingface.co/zai-org/GLM-5.1"],
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
    voices: Annotated[
        list[str] | None,
        Field(
            description="The voices available for this model. Applicable for TTS models and voice-enabled music models. Note: each model has its own set of supported voices.",
            examples=[["Aiden", "Alex", "Alice", "Aria", "Ashley"]],
        ),
    ] = None
    default_voice: Annotated[
        str | None,
        Field(
            description="Default voice for voice-enabled music models.",
            examples=["Aria"],
        ),
    ] = None
    supports_language_code: Annotated[
        bool | None,
        Field(
            description="Whether this music model supports an ISO 639-1 language_code parameter.",
            examples=[True],
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
            description="Supported audio formats for this music model.",
            examples=[["mp3", "wav"]],
        ),
    ] = None
    default_format: Annotated[
        str | None,
        Field(description="Default audio format for this music model.", examples=["mp3"]),
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


class Type49(Enum):
    asr = "asr"
    embedding = "embedding"
    image = "image"
    music = "music"
    text = "text"
    tts = "tts"
    upscale = "upscale"
    inpaint = "inpaint"
    video = "video"


class ModelResponse(VeniceBaseModel):
    created: Annotated[
        float | None,
        Field(description="Release date on Venice API", examples=[1699000000]),
    ] = None
    id: Annotated[str, Field(description="Model ID", examples=["zai-org-glm-5-1"])]
    model_spec: ModelSpec
    object: Annotated[Object1, Field(description="Object type", examples=["model"])]
    owned_by: Annotated[OwnedBy, Field(description="Who runs the model", examples=["venice.ai"])]
    type: Annotated[Type49, Field(description="Model type", examples=["text"])]


class ModelTraitSchema(RootModel[dict[str, str]]):
    root: dict[str, str]


class ModelCompatibilitySchema(RootModel[dict[str, str]]):
    root: dict[str, str]


class Format3(Enum):
    markdown = "markdown"


class WebScrapeResponse(VeniceBaseModel):
    url: Annotated[
        str,
        Field(description="The URL that was scraped", examples=["https://example.com"]),
    ]
    content: Annotated[str, Field(description="The scraped content in markdown format")]
    format: Annotated[Format3, Field(description="The format of the scraped content")]


class Result(VeniceBaseModel):
    title: Annotated[str, Field(description="The title of the search result")]
    url: Annotated[str, Field(description="The URL of the search result")]
    content: Annotated[str, Field(description="A snippet or description of the search result")]
    date: Annotated[str, Field(description="The date of the search result, if available")]


class WebSearchResponse(VeniceBaseModel):
    query: Annotated[str, Field(description="The search query that was executed")]
    results: Annotated[list[Result], Field(description="The search results")]
