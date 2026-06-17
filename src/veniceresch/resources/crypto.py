"""``/crypto/rpc/*`` resource: blockchain JSON-RPC proxy.

Two endpoints:

* ``GET /crypto/rpc/networks`` — public list of supported network slugs.
* ``POST /crypto/rpc/{network}`` — proxy a JSON-RPC 2.0 request (or a batch
  array of up to 100) to a supported chain, billed per credit.

The proxy accepts a single JSON-RPC object or a list of them; the response
mirrors that shape (object for single, array for batch), so :meth:`rpc`
returns the decoded JSON verbatim (``dict`` or ``list``) rather than a typed
wrapper. Per-request JSON-RPC failures come back as HTTP 200 with an
``error`` field on the relevant item — they are *not* raised as exceptions.

Auth: the proxy takes either the default Bearer API key or a wallet
``SIGN-IN-WITH-X`` header (x402). Pass ``siwx_header=`` to use wallet auth;
the default bearer is then stripped. ``Idempotency-Key`` enables safe retries.
``GET /crypto/rpc/networks`` is public and needs no auth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from veniceresch.types import CryptoRpcNetworksResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient

JsonRpcRequest = dict[str, Any] | list[dict[str, Any]]


def _rpc_headers(
    *,
    siwx_header: str | None,
    idempotency_key: str | None,
) -> dict[str, str] | None:
    headers: dict[str, str] = {}
    if siwx_header is not None:
        headers["SIGN-IN-WITH-X"] = siwx_header
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers or None


class AsyncCryptoResource:
    """Async crypto RPC resource. Accessed via ``client.crypto``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def networks(self) -> CryptoRpcNetworksResponse:
        """List the network slugs accepted by :meth:`rpc`. Public — no auth."""
        raw = await self._client._request_json(
            "GET",
            "/crypto/rpc/networks",
            no_auth=True,
        )
        return CryptoRpcNetworksResponse.model_validate(raw)

    async def rpc(
        self,
        network: str,
        request: JsonRpcRequest,
        *,
        siwx_header: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Proxy a JSON-RPC request (or batch list) to ``network``.

        ``request`` is a single JSON-RPC 2.0 object
        (``{"jsonrpc": "2.0", "method": ..., "params": [...], "id": 1}``) or a
        list of up to 100 of them. The return value mirrors that shape — a
        ``dict`` for a single call, a ``list`` for a batch. JSON-RPC-level
        failures surface as an ``error`` field on the response item (HTTP 200),
        not as an exception.
        """
        raw = await self._client._request_any(
            "POST",
            f"/crypto/rpc/{network}",
            json_body=request,
            headers=_rpc_headers(siwx_header=siwx_header, idempotency_key=idempotency_key),
            no_auth=siwx_header is not None,
        )
        return cast("dict[str, Any] | list[Any]", raw)


class CryptoResource:
    """Sync crypto RPC resource. Accessed via ``client.crypto``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def networks(self) -> CryptoRpcNetworksResponse:
        """List the network slugs accepted by :meth:`rpc`. Public — no auth."""
        raw = self._client._request_json(
            "GET",
            "/crypto/rpc/networks",
            no_auth=True,
        )
        return CryptoRpcNetworksResponse.model_validate(raw)

    def rpc(
        self,
        network: str,
        request: JsonRpcRequest,
        *,
        siwx_header: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Sync mirror of :meth:`AsyncCryptoResource.rpc`."""
        raw = self._client._request_any(
            "POST",
            f"/crypto/rpc/{network}",
            json_body=request,
            headers=_rpc_headers(siwx_header=siwx_header, idempotency_key=idempotency_key),
            no_auth=siwx_header is not None,
        )
        return cast("dict[str, Any] | list[Any]", raw)


__all__ = ["AsyncCryptoResource", "CryptoResource"]
