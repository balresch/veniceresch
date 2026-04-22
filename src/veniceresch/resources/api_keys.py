"""``/api_keys/*`` resource: list, create, update, delete, rate limits, web3.

Most methods here require an **admin**-scope API key (Venice's inference
keys don't grant access to key management). The two ``generate_web3_key``
methods are anonymous — they mint a key via wallet signature — and are
called with ``no_auth=True`` so the default ``Authorization`` header is
stripped.

Request-body and query-parameter keys are camelCase in Venice's swagger;
the Python API accepts snake_case and translates (``api_key_type →
apiKeyType``, ``consumption_limit → consumptionLimit``, ``expires_at →
expiresAt``) — same convention as ``model_id → modelId`` elsewhere.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from veniceresch.types import (
    ApiKeyCreateResponse,
    ApiKeyDeleteResponse,
    ApiKeyDetailResponse,
    ApiKeyListResponse,
    ApiKeyRateLimitLogsResponse,
    ApiKeyRateLimitsResponse,
    ApiKeyUpdateResponse,
    Web3KeyChallengeResponse,
    Web3KeyCreateResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


def _create_body(
    *,
    api_key_type: str,
    description: str,
    consumption_limit: dict[str, Any] | None,
    expires_at: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "apiKeyType": api_key_type,
        "description": description,
    }
    if consumption_limit is not None:
        body["consumptionLimit"] = consumption_limit
    if expires_at is not None:
        body["expiresAt"] = expires_at
    return body


def _update_body(
    *,
    id: str,
    description: str | None,
    consumption_limit: dict[str, Any] | None,
    expires_at: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"id": id}
    if description is not None:
        body["description"] = description
    if consumption_limit is not None:
        body["consumptionLimit"] = consumption_limit
    if expires_at is not None:
        body["expiresAt"] = expires_at
    return body


def _web3_create_body(
    *,
    api_key_type: str,
    address: str,
    signature: str,
    token: str,
    description: str | None,
    consumption_limit: dict[str, Any] | None,
    expires_at: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "apiKeyType": api_key_type,
        "address": address,
        "signature": signature,
        "token": token,
    }
    if description is not None:
        body["description"] = description
    if consumption_limit is not None:
        body["consumptionLimit"] = consumption_limit
    if expires_at is not None:
        body["expiresAt"] = expires_at
    return body


class AsyncApiKeysResource:
    """Async api_keys resource. Accessed via ``client.api_keys``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def list(self) -> ApiKeyListResponse:
        raw = await self._client._request_json("GET", "/api_keys")
        return ApiKeyListResponse.model_validate(raw)

    async def get(self, id: str) -> ApiKeyDetailResponse:
        raw = await self._client._request_json("GET", f"/api_keys/{id}")
        return ApiKeyDetailResponse.model_validate(raw)

    async def create(
        self,
        *,
        api_key_type: str,
        description: str,
        consumption_limit: dict[str, Any] | None = None,
        expires_at: str | None = None,
    ) -> ApiKeyCreateResponse:
        body = _create_body(
            api_key_type=api_key_type,
            description=description,
            consumption_limit=consumption_limit,
            expires_at=expires_at,
        )
        raw = await self._client._request_json("POST", "/api_keys", json_body=body)
        return ApiKeyCreateResponse.model_validate(raw)

    async def update(
        self,
        *,
        id: str,
        description: str | None = None,
        consumption_limit: dict[str, Any] | None = None,
        expires_at: str | None = None,
    ) -> ApiKeyUpdateResponse:
        body = _update_body(
            id=id,
            description=description,
            consumption_limit=consumption_limit,
            expires_at=expires_at,
        )
        raw = await self._client._request_json("PATCH", "/api_keys", json_body=body)
        return ApiKeyUpdateResponse.model_validate(raw)

    async def delete(self, id: str) -> ApiKeyDeleteResponse:
        raw = await self._client._request_json("DELETE", "/api_keys", params={"id": id})
        return ApiKeyDeleteResponse.model_validate(raw)

    async def rate_limits(self) -> ApiKeyRateLimitsResponse:
        raw = await self._client._request_json("GET", "/api_keys/rate_limits")
        return ApiKeyRateLimitsResponse.model_validate(raw)

    async def rate_limits_log(self) -> ApiKeyRateLimitLogsResponse:
        raw = await self._client._request_json("GET", "/api_keys/rate_limits/log")
        return ApiKeyRateLimitLogsResponse.model_validate(raw)

    async def generate_web3_key_challenge(self) -> Web3KeyChallengeResponse:
        """Fetch the SIWE challenge token to sign with the wallet's private key."""
        raw = await self._client._request_json(
            "GET",
            "/api_keys/generate_web3_key",
            no_auth=True,
        )
        return Web3KeyChallengeResponse.model_validate(raw)

    async def generate_web3_key(
        self,
        *,
        api_key_type: str,
        address: str,
        signature: str,
        token: str,
        description: str | None = None,
        consumption_limit: dict[str, Any] | None = None,
        expires_at: str | None = None,
    ) -> Web3KeyCreateResponse:
        """Mint an API key from a signed SIWE challenge.

        Call :meth:`generate_web3_key_challenge` first to obtain ``token``;
        sign it with the wallet's private key to produce ``signature``,
        then pass both back here along with the wallet ``address``.
        """
        body = _web3_create_body(
            api_key_type=api_key_type,
            address=address,
            signature=signature,
            token=token,
            description=description,
            consumption_limit=consumption_limit,
            expires_at=expires_at,
        )
        raw = await self._client._request_json(
            "POST",
            "/api_keys/generate_web3_key",
            json_body=body,
            no_auth=True,
        )
        return Web3KeyCreateResponse.model_validate(raw)


class ApiKeysResource:
    """Sync api_keys resource. Accessed via ``client.api_keys``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def list(self) -> ApiKeyListResponse:
        raw = self._client._request_json("GET", "/api_keys")
        return ApiKeyListResponse.model_validate(raw)

    def get(self, id: str) -> ApiKeyDetailResponse:
        raw = self._client._request_json("GET", f"/api_keys/{id}")
        return ApiKeyDetailResponse.model_validate(raw)

    def create(
        self,
        *,
        api_key_type: str,
        description: str,
        consumption_limit: dict[str, Any] | None = None,
        expires_at: str | None = None,
    ) -> ApiKeyCreateResponse:
        body = _create_body(
            api_key_type=api_key_type,
            description=description,
            consumption_limit=consumption_limit,
            expires_at=expires_at,
        )
        raw = self._client._request_json("POST", "/api_keys", json_body=body)
        return ApiKeyCreateResponse.model_validate(raw)

    def update(
        self,
        *,
        id: str,
        description: str | None = None,
        consumption_limit: dict[str, Any] | None = None,
        expires_at: str | None = None,
    ) -> ApiKeyUpdateResponse:
        body = _update_body(
            id=id,
            description=description,
            consumption_limit=consumption_limit,
            expires_at=expires_at,
        )
        raw = self._client._request_json("PATCH", "/api_keys", json_body=body)
        return ApiKeyUpdateResponse.model_validate(raw)

    def delete(self, id: str) -> ApiKeyDeleteResponse:
        raw = self._client._request_json("DELETE", "/api_keys", params={"id": id})
        return ApiKeyDeleteResponse.model_validate(raw)

    def rate_limits(self) -> ApiKeyRateLimitsResponse:
        raw = self._client._request_json("GET", "/api_keys/rate_limits")
        return ApiKeyRateLimitsResponse.model_validate(raw)

    def rate_limits_log(self) -> ApiKeyRateLimitLogsResponse:
        raw = self._client._request_json("GET", "/api_keys/rate_limits/log")
        return ApiKeyRateLimitLogsResponse.model_validate(raw)

    def generate_web3_key_challenge(self) -> Web3KeyChallengeResponse:
        raw = self._client._request_json(
            "GET",
            "/api_keys/generate_web3_key",
            no_auth=True,
        )
        return Web3KeyChallengeResponse.model_validate(raw)

    def generate_web3_key(
        self,
        *,
        api_key_type: str,
        address: str,
        signature: str,
        token: str,
        description: str | None = None,
        consumption_limit: dict[str, Any] | None = None,
        expires_at: str | None = None,
    ) -> Web3KeyCreateResponse:
        body = _web3_create_body(
            api_key_type=api_key_type,
            address=address,
            signature=signature,
            token=token,
            description=description,
            consumption_limit=consumption_limit,
            expires_at=expires_at,
        )
        raw = self._client._request_json(
            "POST",
            "/api_keys/generate_web3_key",
            json_body=body,
            no_auth=True,
        )
        return Web3KeyCreateResponse.model_validate(raw)


__all__ = ["ApiKeysResource", "AsyncApiKeysResource"]
