"""Unit tests for the shared multipart-upload helper (``resources/_uploads``)."""

from __future__ import annotations

import io

import pytest

from veniceresch.resources._uploads import open_upload


def test_bytes_yields_default_name_and_buffers():
    with open_upload(b"raw", default_name="audio.bin") as (name, content, ctype):
        assert name == "audio.bin"
        assert content == b"raw"
        assert ctype == "application/octet-stream"


def test_path_streams_handle_and_closes_after(tmp_path):
    p = tmp_path / "clip.wav"
    p.write_bytes(b"WAVDATA")
    with open_upload(p, default_name="audio.bin") as (name, content, _ctype):
        assert name == "clip.wav"
        # Streamed as an open file handle, not pre-read into bytes.
        assert hasattr(content, "read")
        assert not content.closed
        handle = content
    # The handle we opened ourselves is closed on exit.
    assert handle.closed


def test_string_path_is_treated_as_path(tmp_path):
    p = tmp_path / "doc.bin"
    p.write_bytes(b"DATA")
    with open_upload(str(p), default_name="x.bin") as (name, content, _ctype):
        assert name == "doc.bin"
        assert content.read() == b"DATA"


def test_missing_path_raises_filenotfound(tmp_path):
    missing = tmp_path / "nope.wav"
    with pytest.raises(FileNotFoundError), open_upload(missing, default_name="audio.bin"):
        pass


def test_file_like_passed_through_and_not_closed():
    buf = io.BytesIO(b"inmem")
    with open_upload(buf, default_name="audio.bin") as (name, content, _ctype):
        # No ``.name`` on a bare BytesIO → default name.
        assert name == "audio.bin"
        assert content is buf
    # Caller owns the handle; we must not close it.
    assert not buf.closed
    assert buf.read() == b"inmem"


def test_file_like_name_basename_is_extracted(tmp_path):
    p = tmp_path / "real.mp3"
    p.write_bytes(b"MP3")
    with p.open("rb") as handle:
        with open_upload(handle, default_name="audio.bin") as (name, content, _ctype):
            # ``handle.name`` is a full path; only the basename is reported.
            assert name == "real.mp3"
            assert content is handle
        # An open caller handle stays open after the context exits.
        assert not handle.closed
