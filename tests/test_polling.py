"""Parity tests for the shared audio/video job-failure machinery (_polling.py).

Item #12 collapsed the duplicated failure-status set, predicates, and error
bodies onto one module. These tests pin that the two resources stay in lockstep:
both raise on the *same* status strings and share one error hierarchy, so a
future edit to the failure set can't silently diverge between them.
"""

from __future__ import annotations

import pytest

from veniceresch import (
    VeniceAudioFailedError,
    VeniceJobFailedError,
    VeniceVideoFailedError,
)
from veniceresch.resources._polling import (
    _FAILURE_STATUSES,
    is_failure_status,
    is_processing,
)
from veniceresch.resources._polling import (
    VeniceJobFailedError as _BaseFromModule,
)

# Drive the parity checks off the single shared set, so adding a status there
# automatically exercises both resources here.
_FAILURE_CASES = sorted(_FAILURE_STATUSES)


@pytest.mark.parametrize("status", _FAILURE_CASES)
async def test_both_resources_raise_on_same_failure_status(async_client, mock_api, status):
    """Audio and video must both raise on every status in the shared set."""
    mock_api.post("/audio/retrieve").respond(200, json={"status": status})
    mock_api.post("/video/retrieve").respond(200, json={"status": status})

    with pytest.raises(VeniceAudioFailedError):
        await async_client.audio.wait_for_completion(
            model="a1", queue_id="q", timeout_s=5.0, poll_interval_s=0.01, raise_on_failed=True
        )
    with pytest.raises(VeniceVideoFailedError):
        await async_client.video.wait_for_completion(
            model="v1", queue_id="q", timeout_s=5.0, poll_interval_s=0.01, raise_on_failed=True
        )


def test_failed_errors_share_one_hierarchy():
    """Both named errors subclass the shared base so callers can catch either."""
    assert issubclass(VeniceAudioFailedError, VeniceJobFailedError)
    assert issubclass(VeniceVideoFailedError, VeniceJobFailedError)
    # The re-export and the module class are the same object.
    assert VeniceJobFailedError is _BaseFromModule


def test_predicates_are_case_insensitive():
    assert is_processing("processing")
    assert is_processing("PROCESSING")
    assert not is_processing("done")
    assert not is_processing(None)
    assert is_failure_status("failed")
    assert is_failure_status("CANCELLED")
    assert not is_failure_status("COMPLETED")
    assert not is_failure_status(None)
