"""Shared multipart-upload helpers for the file-accepting resources.

``/audio/transcriptions``, ``/audio/voices`` and ``/augment/text-parser`` send
the file as a multipart upload. Callers may pass any of:

- ``bytes`` — raw file contents. Sent as-is (already in memory; nothing to
  stream).
- ``str`` / :class:`pathlib.Path` — a filesystem path. The file is opened and
  *streamed* to the server by httpx rather than read fully into memory first.
- a binary file-like object (anything with ``.read()``, e.g. an open
  ``"rb"`` handle, :class:`io.BytesIO`, or a Django ``UploadedFile``) — handed
  straight to httpx and streamed. The caller owns the object's lifecycle; we
  never close a handle we did not open.

:func:`open_upload` is a context manager so a path we open ourselves is closed
once the request completes, while a caller-supplied handle is left untouched.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any

# Public input alias shared by the audio and augment resources.
UploadInput = bytes | str | Path | IO[bytes]

_OCTET_STREAM = "application/octet-stream"


@contextmanager
def open_upload(file: UploadInput, *, default_name: str) -> Iterator[tuple[str, Any, str]]:
    """Yield an httpx multipart ``(filename, content, content_type)`` tuple.

    ``content`` is raw ``bytes`` for a bytes input, or an open binary file
    object (which httpx streams) for a path or a caller-supplied handle. Paths
    we open here are closed on exit; caller-supplied handles are left open.

    ``default_name`` is the filename reported to the server when the input
    carries none of its own (raw bytes, or a file-like object without a usable
    ``.name``).
    """
    if isinstance(file, bytes):
        yield (default_name, file, _OCTET_STREAM)
        return
    if isinstance(file, (str, Path)):
        path = Path(file)
        with path.open("rb") as handle:
            yield (path.name, handle, _OCTET_STREAM)
        return
    # File-like object: stream it, but never close the caller's handle. Derive a
    # filename from ``.name`` when it is a real path string (skip int fds).
    name = getattr(file, "name", None)
    filename = Path(name).name if isinstance(name, str) and name else default_name
    yield (filename, file, _OCTET_STREAM)


__all__ = ["UploadInput", "open_upload"]
