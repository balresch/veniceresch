"""Smoke test — placeholder until real tests arrive in Phase 2+."""

from venice_sdk import __version__


def test_version_is_set() -> None:
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 2
