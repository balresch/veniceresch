"""Shared queue/retrieve polling machinery for the audio and video resources.

Both ``/audio/*`` and ``/video/*`` expose the same queue → poll-``retrieve`` →
terminal-state flow, so the status vocabulary and the failure-error shape are
identical across the two resources. They lived as verbatim copies in
``audio.py`` and ``video.py``; this module is the single home so a new terminal
failure string (or a casing fix) is changed once, not twice.

What is *not* here: the resource classes themselves. CLAUDE.md keeps the
sync/async surfaces and the two resource modules deliberately distinct; this is
shared *constants + predicates + an error base*, not a resource refactor.
"""

from __future__ import annotations

from typing import Any, TypeGuard

from veniceresch._errors import VeniceAPIError

_STATUS_PROCESSING = "PROCESSING"
# Venice does not document failure status strings for the queue/retrieve
# endpoints (the swagger status enums list only PROCESSING / COMPLETED). This
# curated, case-insensitive set is what ``wait_for_completion(raise_on_failed=
# True)`` treats as failure; any other non-PROCESSING status (including unknown
# ones) still returns normally, preserving the "tolerate unknown terminal
# statuses" contract.
_FAILURE_STATUSES = frozenset({"FAILED", "CANCELLED", "CANCELED", "ERROR"})


def is_processing(status: Any) -> bool:
    """True while the job is still in progress (case-insensitive ``PROCESSING``).

    The comparison is case-insensitive so a ``"processing"`` / ``"Processing"``
    variant does not look terminal and end the wait mid-job. Only this in-progress
    check is case-insensitive — the set of statuses treated as terminal is still
    "anything not processing," preserving tolerance of unknown terminal statuses.
    """
    return isinstance(status, str) and status.upper() == _STATUS_PROCESSING


def is_failure_status(status: Any) -> TypeGuard[str]:
    """True for a known, curated failure terminal status (case-insensitive).

    Narrows to ``str`` (a :class:`~typing.TypeGuard`) so callers can pass the
    status straight to a ``*FailedError`` constructor without re-checking it.
    """
    return isinstance(status, str) and status.upper() in _FAILURE_STATUSES


class VeniceJobFailedError(VeniceAPIError):
    """Base for the queued audio/video job-failure errors.

    Raised by ``wait_for_completion(raise_on_failed=True)`` when a job reaches a
    known failure terminal state (see :data:`_FAILURE_STATUSES`). The final
    retrieve response is on :attr:`result` for inspection. Catch this base to
    handle both :class:`VeniceAudioFailedError` and ``VeniceVideoFailedError``.
    """

    def __init__(self, queue_id: str, status: str, result: Any, *, kind: str) -> None:
        super().__init__(
            f"{kind} queue_id={queue_id!r} ended in failure status {status!r}",
            status_code=0,
            error_body={"queue_id": queue_id, "status": status},
        )
        self.queue_id = queue_id
        self.status = status
        self.result = result


__all__ = [
    "VeniceJobFailedError",
    "is_failure_status",
    "is_processing",
]
