"""Auto-paginating iterators for Venice list endpoints.

Venice list endpoints come in two flavors — offset-based
(``limit``/``offset``) and page-based (``limit``/``page``) — with three
different end-of-data signals (``hasMore``, ``totalPages``, or "short
page"). Rather than bake those variations into a shared strategy enum,
each resource method passes three small closures to the paginator:

* ``fetch(params)`` — issue one HTTP call for a page of data.
* ``extract(page)`` — pull the items list out of the response wrapper.
* ``step(page, params)`` — return the params dict for the next page, or
  ``None`` when done.

The paginator itself is endpoint-agnostic. Iteration is lazy: no HTTP
request fires until ``async for`` / ``for`` actually starts. Items are
yielded one at a time across page boundaries; ``iter_pages()`` yields
the raw response object per page.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Any, Generic, TypeVar

ItemT = TypeVar("ItemT")
PageT = TypeVar("PageT")


class AsyncPaginator(Generic[ItemT, PageT]):
    """Async auto-paginator. Returned by ``client.<resource>.iter_*`` methods.

    Usage::

        async for item in client.x402.iter_transactions(wallet, siwx_header=...):
            ...

        # or page-by-page:
        async for page in client.x402.iter_transactions(wallet, siwx_header=...).iter_pages():
            ...
    """

    def __init__(
        self,
        *,
        fetch: Callable[[dict[str, Any]], Awaitable[PageT]],
        initial_params: dict[str, Any],
        extract: Callable[[PageT], list[ItemT]],
        step: Callable[[PageT, dict[str, Any]], dict[str, Any] | None],
    ) -> None:
        self._fetch = fetch
        self._initial_params = initial_params
        self._extract = extract
        self._step = step

    def __aiter__(self) -> AsyncIterator[ItemT]:
        return self._iter_items()

    async def _iter_items(self) -> AsyncIterator[ItemT]:
        async for page in self.iter_pages():
            for item in self._extract(page):
                yield item

    async def iter_pages(self) -> AsyncIterator[PageT]:
        """Yield each page response in order. Fetches lazily, one page at a time."""
        params = dict(self._initial_params)
        while True:
            page = await self._fetch(params)
            yield page
            next_params = self._step(page, params)
            if next_params is None:
                return
            params = next_params


class Paginator(Generic[ItemT, PageT]):
    """Sync auto-paginator. Sync mirror of :class:`AsyncPaginator`.

    Usage::

        for item in client.x402.iter_transactions(wallet, siwx_header=...):
            ...

        for page in client.x402.iter_transactions(wallet, siwx_header=...).iter_pages():
            ...
    """

    def __init__(
        self,
        *,
        fetch: Callable[[dict[str, Any]], PageT],
        initial_params: dict[str, Any],
        extract: Callable[[PageT], list[ItemT]],
        step: Callable[[PageT, dict[str, Any]], dict[str, Any] | None],
    ) -> None:
        self._fetch = fetch
        self._initial_params = initial_params
        self._extract = extract
        self._step = step

    def __iter__(self) -> Iterator[ItemT]:
        for page in self.iter_pages():
            yield from self._extract(page)

    def iter_pages(self) -> Iterator[PageT]:
        """Yield each page response in order. Fetches lazily, one page at a time."""
        params = dict(self._initial_params)
        while True:
            page = self._fetch(params)
            yield page
            next_params = self._step(page, params)
            if next_params is None:
                return
            params = next_params


__all__ = ["AsyncPaginator", "Paginator"]
