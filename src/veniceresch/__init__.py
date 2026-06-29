"""veniceresch — typed, async-first Python client for the Venice.ai API."""

from veniceresch._client import AsyncVeniceClient, VeniceClient
from veniceresch._errors import (
    VeniceAPIError,
    VeniceAuthError,
    VeniceConnectionError,
    VeniceContentViolationError,
    VeniceError,
    VeniceInsufficientBalanceError,
    VeniceNotFoundError,
    VenicePayloadTooLargeError,
    VeniceProviderContentPolicyError,
    VeniceRateLimitError,
    VeniceServerError,
    VeniceTimeoutError,
    VeniceUnexpectedContentTypeError,
    VeniceValidationError,
    VeniceX402PaymentRequiredError,
)
from veniceresch._version import __version__
from veniceresch.pagination import AsyncPaginator, Paginator
from veniceresch.resources._polling import VeniceJobFailedError
from veniceresch.resources.audio import VeniceAudioFailedError, VeniceAudioTimeoutError
from veniceresch.resources.video import VeniceVideoFailedError, VeniceVideoTimeoutError

__all__ = [
    "AsyncPaginator",
    "AsyncVeniceClient",
    "Paginator",
    "VeniceAPIError",
    "VeniceAudioFailedError",
    "VeniceAudioTimeoutError",
    "VeniceAuthError",
    "VeniceClient",
    "VeniceConnectionError",
    "VeniceContentViolationError",
    "VeniceError",
    "VeniceInsufficientBalanceError",
    "VeniceJobFailedError",
    "VeniceNotFoundError",
    "VenicePayloadTooLargeError",
    "VeniceProviderContentPolicyError",
    "VeniceRateLimitError",
    "VeniceServerError",
    "VeniceTimeoutError",
    "VeniceUnexpectedContentTypeError",
    "VeniceValidationError",
    "VeniceVideoFailedError",
    "VeniceVideoTimeoutError",
    "VeniceX402PaymentRequiredError",
    "__version__",
]
