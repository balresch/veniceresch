"""Single source of truth for the package version.

The version is declared once in ``pyproject.toml`` (``project.version``) and
read back here from the installed package metadata, so there is nothing to
hand-bump in this file. ``importlib.metadata.version`` resolves against the
installed distribution; the editable/local fallback keeps imports working when
the package isn't installed (e.g. running straight from a source checkout).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("veniceresch")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
