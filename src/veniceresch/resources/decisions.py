"""``/decisions`` resource (beta): typed judgments over a state.

**Beta** — Venice marks this endpoint as unstable; request/response shapes may
change without notice, which is why answers are surfaced as plain dicts.

You send a ``state`` (a string, or structured JSON such as a chat log or a
record) and a map of typed ``questions``; every question is evaluated in
parallel against that state and comes back as a structured answer under the
same key. Question types:

- ``{"type": "noul", "instructions": "...", "criteria": {"true": ..., "false": ...}}``
  — a yes/no probability (``criteria`` optional);
- ``{"type": "choice", "instructions": "...", "criteria": {"option": "rubric" | None, ...}}``
  — pick one option, with the full probability distribution;
- ``{"type": "score", "instructions": "...", "criteria": ["lowest", ..., "highest"]}``
  — a probability-weighted position on an ordered rubric (≥ 2 levels).

``POST /systemone`` is a byte-for-byte alias of ``/decisions`` kept upstream
for TypeSafe-SDK compatibility; this SDK only calls ``/decisions``. List the
available models with ``client.models.list(type="decision")``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from veniceresch.types import DecisionResponse

if TYPE_CHECKING:
    from veniceresch._client import AsyncVeniceClient, VeniceClient


# A ``data:image/png;base64,...`` URI, or ``{"content_type": ..., "base64": ...}``.
DecisionImage = str | Mapping[str, str]


def _decision_body(
    *,
    model: str,
    state: Any,
    questions: Mapping[str, Mapping[str, Any]],
    images: Sequence[DecisionImage] | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "state": state,
        "questions": {k: dict(v) for k, v in questions.items()},
    }
    if images is not None:
        body["images"] = [img if isinstance(img, str) else dict(img) for img in images]
    body.update({k: v for k, v in extra.items() if v is not None})
    return body


class AsyncDecisionsResource:
    """Async decisions resource (beta). Accessed via ``client.decisions``."""

    def __init__(self, client: AsyncVeniceClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        state: Any,
        questions: Mapping[str, Mapping[str, Any]],
        images: Sequence[DecisionImage] | None = None,
        **extra: Any,
    ) -> DecisionResponse:
        """Evaluate ``state`` against ``questions``; returns one answer per key.

        ``images`` (up to 4) must be inline — ``data:`` URIs or
        ``{"content_type": "image/png", "base64": "..."}`` objects; Venice does
        not fetch remote URLs here.
        """
        body = _decision_body(
            model=model, state=state, questions=questions, images=images, extra=extra
        )
        raw = await self._client._request_json("POST", "/decisions", json_body=body)
        return DecisionResponse.model_validate(raw)


class DecisionsResource:
    """Sync decisions resource (beta). Accessed via ``client.decisions``."""

    def __init__(self, client: VeniceClient) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        state: Any,
        questions: Mapping[str, Mapping[str, Any]],
        images: Sequence[DecisionImage] | None = None,
        **extra: Any,
    ) -> DecisionResponse:
        """Sync mirror of :meth:`AsyncDecisionsResource.create`."""
        body = _decision_body(
            model=model, state=state, questions=questions, images=images, extra=extra
        )
        raw = self._client._request_json("POST", "/decisions", json_body=body)
        return DecisionResponse.model_validate(raw)


__all__ = ["AsyncDecisionsResource", "DecisionImage", "DecisionsResource"]
