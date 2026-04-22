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
    VeniceRateLimitError,
    VeniceServerError,
    VeniceTimeoutError,
    VeniceValidationError,
    VeniceX402PaymentRequiredError,
)
from veniceresch._version import __version__
from veniceresch.pagination import AsyncPaginator, Paginator
from veniceresch.resources.audio import VeniceAudioTimeoutError
from veniceresch.resources.video import VeniceVideoTimeoutError

__all__ = [
    "AsyncPaginator",
    "AsyncVeniceClient",
    "Paginator",
    "VeniceAPIError",
    "VeniceAudioTimeoutError",
    "VeniceAuthError",
    "VeniceClient",
    "VeniceConnectionError",
    "VeniceContentViolationError",
    "VeniceError",
    "VeniceInsufficientBalanceError",
    "VeniceNotFoundError",
    "VeniceRateLimitError",
    "VeniceServerError",
    "VeniceTimeoutError",
    "VeniceValidationError",
    "VeniceVideoTimeoutError",
    "VeniceX402PaymentRequiredError",
    "__version__",
]
