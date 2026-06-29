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

:func:`open_upload` (sync) is a context manager so a path we open ourselves is
closed once the request completes, while a caller-supplied handle is left
untouched.

:func:`async_open_upload` is the async counterpart. httpx's async multipart
encoder reads a file handle with *synchronous* ``.read()`` calls inside the
request coroutine, so streaming a path/handle the way :func:`open_upload` does
would keep disk I/O on the event loop for the whole upload. To avoid that, the
async helper reads the file fully in a worker thread (:func:`asyncio.to_thread`)
and hands httpx the resulting ``bytes`` — trading streaming for an unblocked
loop. ``bytes`` inputs are already in memory and are yielded as-is on both
paths.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
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


@asynccontextmanager
async def async_open_upload(
    file: UploadInput, *, default_name: str
) -> AsyncIterator[tuple[str, Any, str]]:
    """Async counterpart to :func:`open_upload` that never blocks the loop.

    Unlike the sync helper, ``content`` is always raw ``bytes``: a path or a
    caller-supplied handle is read in full in a worker thread
    (:func:`asyncio.to_thread`) so the disk I/O leaves the event loop, then the
    bytes are handed to httpx. This gives up streaming on the async path (see
    the module docstring) in exchange for not stalling other coroutines for the
    duration of the request. A caller-supplied handle is read but never closed —
    the caller owns its lifecycle.
    """
    if isinstance(file, bytes):
        yield (default_name, file, _OCTET_STREAM)
        return
    if isinstance(file, (str, Path)):
        path = Path(file)
        data = await asyncio.to_thread(path.read_bytes)
        yield (path.name, data, _OCTET_STREAM)
        return
    # File-like object: read it off-thread; derive a filename from ``.name``
    # when it is a real path string (skip int fds). Never close the handle.
    name = getattr(file, "name", None)
    filename = Path(name).name if isinstance(name, str) and name else default_name
    data = await asyncio.to_thread(file.read)
    yield (filename, data, _OCTET_STREAM)


__all__ = ["UploadInput", "async_open_upload", "open_upload"]
