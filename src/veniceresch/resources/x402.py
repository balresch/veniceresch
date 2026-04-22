"""``/x402/*`` resource: wallet balance, top-up, and transaction history.

All three endpoints use wallet-based auth rather than the bearer token —
``/x402/balance`` and ``/x402/transactions`` take a SIWE payload in the
``X-Sign-In-With-X`` header, and ``/x402/top-up`` takes a signed x402
payment payload in the ``X-402-Payment`` header. This SDK stops at the
HTTP boundary: callers generate the signed header payloads with whatever
wallet tooling they use and pass them in as strings. Every method here
sends ``no_auth=True`` so the default ``Authorization: Bearer …`` is
stripped.

:meth:`AsyncX402Resource.top_up` returns the success payload when given a
valid ``payment_header``. Calling it with no header (or an invalid one)
makes Venice return a 402 carrying the x402 discovery info; that status
+ body shape is caught by
:func:`veniceresch._errors.raise_for_response` and re-raised as
:class:`~veniceresch.VeniceX402PaymentRequiredError`, whose
``.x402_version`` and ``.accepts`` attrs mirror the response fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from veniceresch.pagination import AsyncPaginator, Paginator
from veniceresch.types import (
    X402BalanceResponse,
    X402TopUpResponse,
    X402TransactionsResponse,
)

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


def _transactions_params(
    *,
    limit: int | None,
    offset: int | None,
) -> dict[str, int] | None:
    params: dict[str, int] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return params or None


def _transactions_items(page: X402TransactionsResponse) -> list[dict[str, Any]]:
    data = page.data or {}
    txs = data.get("transactions")
    return txs if isinstance(txs, list) else []


def _transactions_next(
    page: X402TransactionsResponse,
    params: dict[str, Any],
) -> dict[str, Any] | None:
    # Primary signal: Venice's envelope says whether more pages exist.
    # Fallback: a short page means we've hit the end even if hasMore is missing.
    pagination = (page.data or {}).get("pagination") or {}
    if pagination.get("hasMore") is False:
        return None
    if len(_transactions_items(page)) < params["limit"]:
        return None
    return {"limit": params["limit"], "offset": params["offset"] + params["limit"]}


class AsyncX402Resource:
    """Async x402 resource. Accessed via ``client.x402``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def balance(
        self,
        wallet_address: str,
        *,
        siwx_header: str,
    ) -> X402BalanceResponse:
        """Fetch the x402 credit balance for a wallet.

        ``siwx_header`` is the base64-encoded SIWE payload proving wallet
        ownership — sent as ``X-Sign-In-With-X``.
        """
        raw = await self._client._request_json(
            "GET",
            f"/x402/balance/{wallet_address}",
            headers={"X-Sign-In-With-X": siwx_header},
            no_auth=True,
        )
        return X402BalanceResponse.model_validate(raw)

    async def top_up(
        self,
        *,
        payment_header: str | None = None,
    ) -> X402TopUpResponse:
        """Top up the x402 balance with a signed x402 payment payload.

        Pass ``payment_header`` to attach the ``X-402-Payment`` header.
        Calling without it triggers Venice's 402 payment-required
        discovery flow, which raises
        :class:`~veniceresch.VeniceX402PaymentRequiredError` with the
        accepted payment options on ``.accepts``.
        """
        headers = {"X-402-Payment": payment_header} if payment_header else None
        raw = await self._client._request_json(
            "POST",
            "/x402/top-up",
            headers=headers,
            no_auth=True,
        )
        return X402TopUpResponse.model_validate(raw)

    async def transactions(
        self,
        wallet_address: str,
        *,
        siwx_header: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> X402TransactionsResponse:
        """List x402 ledger entries for a wallet (paginated)."""
        raw = await self._client._request_json(
            "GET",
            f"/x402/transactions/{wallet_address}",
            headers={"X-Sign-In-With-X": siwx_header},
            params=_transactions_params(limit=limit, offset=offset),
            no_auth=True,
        )
        return X402TransactionsResponse.model_validate(raw)

    def iter_transactions(
        self,
        wallet_address: str,
        *,
        siwx_header: str,
        limit: int = 25,
    ) -> AsyncPaginator[dict[str, Any], X402TransactionsResponse]:
        """Auto-paginated iteration over a wallet's x402 ledger.

        ``async for tx in client.x402.iter_transactions(wallet, siwx_header=...)``
        yields each transaction dict; ``iter_pages()`` yields the
        :class:`X402TransactionsResponse` per page. No HTTP calls fire
        until iteration starts.
        """

        async def _fetch(params: dict[str, Any]) -> X402TransactionsResponse:
            return await self.transactions(
                wallet_address,
                siwx_header=siwx_header,
                limit=params["limit"],
                offset=params["offset"],
            )

        return AsyncPaginator(
            fetch=_fetch,
            initial_params={"limit": limit, "offset": 0},
            extract=_transactions_items,
            step=_transactions_next,
        )


class X402Resource:
    """Sync x402 resource. Accessed via ``client.x402``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def balance(
        self,
        wallet_address: str,
        *,
        siwx_header: str,
    ) -> X402BalanceResponse:
        raw = self._client._request_json(
            "GET",
            f"/x402/balance/{wallet_address}",
            headers={"X-Sign-In-With-X": siwx_header},
            no_auth=True,
        )
        return X402BalanceResponse.model_validate(raw)

    def top_up(
        self,
        *,
        payment_header: str | None = None,
    ) -> X402TopUpResponse:
        headers = {"X-402-Payment": payment_header} if payment_header else None
        raw = self._client._request_json(
            "POST",
            "/x402/top-up",
            headers=headers,
            no_auth=True,
        )
        return X402TopUpResponse.model_validate(raw)

    def transactions(
        self,
        wallet_address: str,
        *,
        siwx_header: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> X402TransactionsResponse:
        raw = self._client._request_json(
            "GET",
            f"/x402/transactions/{wallet_address}",
            headers={"X-Sign-In-With-X": siwx_header},
            params=_transactions_params(limit=limit, offset=offset),
            no_auth=True,
        )
        return X402TransactionsResponse.model_validate(raw)

    def iter_transactions(
        self,
        wallet_address: str,
        *,
        siwx_header: str,
        limit: int = 25,
    ) -> Paginator[dict[str, Any], X402TransactionsResponse]:
        """Sync mirror of :meth:`AsyncX402Resource.iter_transactions`."""

        def _fetch(params: dict[str, Any]) -> X402TransactionsResponse:
            return self.transactions(
                wallet_address,
                siwx_header=siwx_header,
                limit=params["limit"],
                offset=params["offset"],
            )

        return Paginator(
            fetch=_fetch,
            initial_params={"limit": limit, "offset": 0},
            extract=_transactions_items,
            step=_transactions_next,
        )


__all__ = ["AsyncX402Resource", "X402Resource"]
