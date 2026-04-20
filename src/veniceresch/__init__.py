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
)
from veniceresch._version import __version__
from veniceresch.resources.audio import VeniceAudioTimeoutError
from veniceresch.resources.video import VeniceVideoTimeoutError

__all__ = [
    "AsyncVeniceClient",
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
    "__version__",
]
