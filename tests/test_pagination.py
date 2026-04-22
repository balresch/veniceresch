"""Tests for the auto-paginating ``iter_*`` methods.

Covers the four paginated endpoints (``x402.iter_transactions``,
``characters.iter_list``, ``characters.iter_reviews``,
``billing.iter_usage``) across async and sync. Also verifies:

* iteration is lazy — no HTTP call fires before ``async for`` / ``for``;
* ``iter_pages()`` yields one page per fetch;
* end-of-data detection stops the loop at the right time and does
  **not** make an extra request after the last page.
"""

from __future__ import annotations

import httpx

from veniceresch import AsyncPaginator, Paginator

# ---- x402.iter_transactions ---------------------------------------------


def _tx_page(offset: int, count: int, *, has_more: bool) -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "walletAddress": "0xabc",
            "currentBalance": 42.0,
            "transactions": [{"id": f"tx_{offset + i}"} for i in range(count)],
            "pagination": {"limit": 25, "offset": offset, "hasMore": has_more},
        },
    }


async def test_iter_transactions_items_exhaust(mock_api, async_client):
    route = mock_api.get("/x402/transactions/0xabc").mock(
        side_effect=[
            httpx.Response(200, json=_tx_page(0, 25, has_more=True)),
            httpx.Response(200, json=_tx_page(25, 25, has_more=True)),
            httpx.Response(200, json=_tx_page(50, 7, has_more=False)),
        ]
    )
    paginator = async_client.x402.iter_transactions("0xabc", siwx_header="siwx")
    assert isinstance(paginator, AsyncPaginator)
    items = [item async for item in paginator]
    assert [i["id"] for i in items] == [f"tx_{n}" for n in range(57)]
    # hasMore=False on page 3 must stop the loop — no 4th request.
    assert route.call_count == 3


async def test_iter_transactions_iter_pages(mock_api, async_client):
    mock_api.get("/x402/transactions/0xabc").mock(
        side_effect=[
            httpx.Response(200, json=_tx_page(0, 25, has_more=True)),
            httpx.Response(200, json=_tx_page(25, 5, has_more=False)),
        ]
    )
    pages = []
    async for page in async_client.x402.iter_transactions("0xabc", siwx_header="siwx").iter_pages():
        pages.append(page)
    assert len(pages) == 2
    assert pages[0].data is not None
    assert len(pages[0].data["transactions"]) == 25
    assert len(pages[1].data["transactions"]) == 5


async def test_iter_transactions_lazy(mock_api, async_client):
    route = mock_api.get("/x402/transactions/0xabc").respond(
        200, json=_tx_page(0, 0, has_more=False)
    )
    # Constructing the paginator must NOT fire a request.
    paginator = async_client.x402.iter_transactions("0xabc", siwx_header="siwx")
    assert route.call_count == 0
    _ = [item async for item in paginator]
    assert route.call_count == 1


async def test_iter_transactions_custom_limit_passthrough(mock_api, async_client):
    route = mock_api.get("/x402/transactions/0xabc").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "walletAddress": "0xabc",
                        "transactions": [{"id": "tx_a"}, {"id": "tx_b"}, {"id": "tx_c"}],
                        "pagination": {"limit": 3, "offset": 0, "hasMore": True},
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "walletAddress": "0xabc",
                        "transactions": [],
                        "pagination": {"limit": 3, "offset": 3, "hasMore": False},
                    },
                },
            ),
        ]
    )
    items = [
        i async for i in async_client.x402.iter_transactions("0xabc", siwx_header="siwx", limit=3)
    ]
    assert [i["id"] for i in items] == ["tx_a", "tx_b", "tx_c"]
    # Every request honored the custom limit and offset advanced by limit.
    assert route.calls[0].request.url.params["limit"] == "3"
    assert route.calls[0].request.url.params["offset"] == "0"
    assert route.calls[1].request.url.params["offset"] == "3"


def test_iter_transactions_sync(mock_api, sync_client):
    route = mock_api.get("/x402/transactions/0xabc").mock(
        side_effect=[
            httpx.Response(200, json=_tx_page(0, 25, has_more=True)),
            httpx.Response(200, json=_tx_page(25, 2, has_more=False)),
        ]
    )
    paginator = sync_client.x402.iter_transactions("0xabc", siwx_header="siwx")
    assert isinstance(paginator, Paginator)
    items = list(paginator)
    assert len(items) == 27
    assert route.call_count == 2


# ---- characters.iter_list (no envelope; stop on short page) -------------


async def test_iter_list_stops_on_short_page(mock_api, async_client):
    route = mock_api.get("/characters").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"object": "list", "data": [{"slug": f"c_{i}"} for i in range(50)]},
            ),
            httpx.Response(
                200,
                json={"object": "list", "data": [{"slug": f"c_{i}"} for i in range(50, 90)]},
            ),
        ]
    )
    items = [c async for c in async_client.characters.iter_list()]
    # First page full (50), second page short (40) → stop, no page 3.
    assert len(items) == 90
    assert route.call_count == 2
    assert route.calls[0].request.url.params["offset"] == "0"
    assert route.calls[1].request.url.params["offset"] == "50"


async def test_iter_list_empty(mock_api, async_client):
    route = mock_api.get("/characters").respond(200, json={"object": "list", "data": []})
    items = [c async for c in async_client.characters.iter_list()]
    assert items == []
    assert route.call_count == 1


def test_iter_list_sync(mock_api, sync_client):
    route = mock_api.get("/characters").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"object": "list", "data": [{"slug": f"c_{i}"} for i in range(10)]},
            ),
            httpx.Response(
                200,
                json={"object": "list", "data": [{"slug": f"c_{i}"} for i in range(10, 15)]},
            ),
        ]
    )
    items = list(sync_client.characters.iter_list(limit=10))
    assert len(items) == 15
    assert route.call_count == 2


# ---- characters.iter_reviews (page-based, totalPages) -------------------


async def test_iter_reviews_stops_on_total_pages(mock_api, async_client):
    route = mock_api.get("/characters/lucy/reviews").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [{"id": f"r{i}"} for i in range(20)],
                    "pagination": {"page": 1, "pageSize": 20, "total": 45, "totalPages": 3},
                    "summary": {"averageRating": 4.5, "totalReviews": 45},
                },
            ),
            httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [{"id": f"r{i}"} for i in range(20, 40)],
                    "pagination": {"page": 2, "pageSize": 20, "total": 45, "totalPages": 3},
                    "summary": {"averageRating": 4.5, "totalReviews": 45},
                },
            ),
            httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [{"id": f"r{i}"} for i in range(40, 45)],
                    "pagination": {"page": 3, "pageSize": 20, "total": 45, "totalPages": 3},
                    "summary": {"averageRating": 4.5, "totalReviews": 45},
                },
            ),
        ]
    )
    items = [r async for r in async_client.characters.iter_reviews("lucy")]
    assert len(items) == 45
    # page >= totalPages on page 3 must stop — no page-4 request.
    assert route.call_count == 3
    assert route.calls[0].request.url.params["page"] == "1"
    assert route.calls[1].request.url.params["page"] == "2"
    assert route.calls[2].request.url.params["page"] == "3"


# ---- billing.iter_usage (page-based, totalPages) ------------------------


async def test_iter_usage_stops_on_total_pages(mock_api, async_client):
    route = mock_api.get("/billing/usage").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": f"u{i}"} for i in range(200)],
                    "pagination": {"limit": 200, "page": 1, "total": 350, "totalPages": 2},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{"id": f"u{i}"} for i in range(200, 350)],
                    "pagination": {"limit": 200, "page": 2, "total": 350, "totalPages": 2},
                },
            ),
        ]
    )
    items = [u async for u in async_client.billing.iter_usage()]
    assert len(items) == 350
    assert route.call_count == 2
    assert route.calls[0].request.url.params["page"] == "1"
    assert route.calls[1].request.url.params["page"] == "2"


def test_iter_usage_sync(mock_api, sync_client):
    route = mock_api.get("/billing/usage").respond(
        200,
        json={
            "data": [{"id": "u1"}, {"id": "u2"}],
            "pagination": {"limit": 200, "page": 1, "total": 2, "totalPages": 1},
        },
    )
    items = list(sync_client.billing.iter_usage())
    assert [u["id"] for u in items] == ["u1", "u2"]
    assert route.call_count == 1
