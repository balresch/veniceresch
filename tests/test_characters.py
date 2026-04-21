"""Tests for the characters resource (list, get, reviews)."""

from __future__ import annotations

import pytest

from veniceresch import VeniceNotFoundError


async def test_list_no_params(mock_api, async_client):
    route = mock_api.get("/characters").respond(
        200,
        json={"object": "list", "data": []},
    )
    await async_client.characters.list()
    assert route.called
    assert route.calls.last.request.url.query == b""


async def test_list_translates_camelcase(mock_api, async_client):
    route = mock_api.get("/characters").respond(
        200,
        json={"object": "list", "data": []},
    )
    await async_client.characters.list(
        is_adult=False,
        is_pro=True,
        is_web_enabled=True,
        sort_by="featured",
        sort_order="desc",
        model_id=["m1", "m2"],
        limit=5,
        offset=10,
        search="alice",
    )
    params = route.calls.last.request.url.params
    # Booleans serialize as lowercase strings (Venice enum).
    assert params["isAdult"] == "false"
    assert params["isPro"] == "true"
    assert params["isWebEnabled"] == "true"
    assert params["sortBy"] == "featured"
    assert params["sortOrder"] == "desc"
    # Array params repeat the key.
    assert params.get_list("modelId") == ["m1", "m2"]
    assert params["limit"] == "5"
    assert params["offset"] == "10"
    assert params["search"] == "alice"


async def test_list_response_parsed(mock_api, async_client):
    mock_api.get("/characters").respond(
        200,
        json={
            "object": "list",
            "data": [{"slug": "lucy", "name": "Lucy"}],
        },
    )
    result = await async_client.characters.list(limit=1)
    assert result.object == "list"
    assert result.data[0]["slug"] == "lucy"


async def test_get_interpolates_slug(mock_api, async_client):
    route = mock_api.get("/characters/lucy").respond(
        200,
        json={"object": "character", "data": {"slug": "lucy", "name": "Lucy"}},
    )
    result = await async_client.characters.get("lucy")
    assert route.called
    assert result.data is not None
    assert result.data["slug"] == "lucy"


async def test_reviews_translates_page_size(mock_api, async_client):
    route = mock_api.get("/characters/lucy/reviews").respond(
        200,
        json={
            "object": "list",
            "data": [{"id": "r1", "rating": 5}],
            "pagination": {"page": 1, "pageSize": 20, "total": 1, "totalPages": 1},
            "summary": {"averageRating": 5, "totalReviews": 1},
        },
    )
    result = await async_client.characters.reviews("lucy", page=1, page_size=20)
    params = route.calls.last.request.url.params
    assert params["page"] == "1"
    assert params["pageSize"] == "20"
    assert result.pagination == {"page": 1, "pageSize": 20, "total": 1, "totalPages": 1}
    assert result.summary == {"averageRating": 5, "totalReviews": 1}
    assert result.data[0]["rating"] == 5


async def test_get_raises_not_found(mock_api, async_client):
    mock_api.get("/characters/missing").respond(404, json={"error": "no such character"})
    with pytest.raises(VeniceNotFoundError):
        await async_client.characters.get("missing")


def test_sync_list(mock_api, sync_client):
    mock_api.get("/characters").respond(
        200,
        json={"object": "list", "data": [{"slug": "lucy"}]},
    )
    result = sync_client.characters.list(limit=1)
    assert result.data[0]["slug"] == "lucy"
