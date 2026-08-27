"""The shipped `cdp.py` fetcher — offline unit tests only.

The file ships in the wheel as **package data** (`src/fux/templates/cdp.py.txt`)
and `fux setup` copies it into the consumer's `.fux/fetchers/cdp.py`, where it
becomes their code (ADR-CDP-FETCHER decision 7). It is never imported by fux —
which is why the extension is one Python's import machinery cannot resolve, and
why these tests have to load it explicitly.

They exercise the pure parts (RFC 6455 framing, handshake key, HTML→markdown,
the contract surface, the `configure` hook). Nothing here opens a socket or
needs Chrome — the CDP session itself is the consumer's to run.
"""

from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

_TEMPLATE = Path(__file__).resolve().parents[2] / "src" / "fux" / "templates" / "cdp.py.txt"


def _load():
    loader = SourceFileLoader("cdp_fetcher_under_test", str(_TEMPLATE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mw():
    return _load()


def test_the_fetcher_ships_as_package_data_and_is_never_imported():
    """ADR-FETCHER's adapter cap, made structural rather than remembered."""
    assert _TEMPLATE.is_file()
    assert _TEMPLATE.suffix == ".txt"  # `import fux.templates.cdp` must not resolve


def test_contract_surface(mw):
    assert callable(mw.fetch)
    assert callable(mw.connect)
    assert callable(mw.close)
    assert callable(mw.configure)


def test_configure_overrides_the_defaults():
    module = _load()  # fresh module: globals are the shipped defaults
    assert module.CDP_PORT == 9222
    module.configure({"cdp_port": 9333, "settle_ms": 0, "launch_chrome": False})
    assert module.CDP_PORT == 9333
    assert module.SETTLE_MS == 0
    assert module.LAUNCH_CHROME is False
    assert module.LOAD_TIMEOUT_S == 30.0  # untouched keys keep their default


def test_configure_rejects_an_unknown_key():
    module = _load()
    with pytest.raises(module.FetcherError, match="unknown key"):
        module.configure({"cdp_prot": 9333})


def test_configure_with_an_empty_table_changes_nothing():
    module = _load()
    module.configure({})
    assert (module.CDP_PORT, module.SETTLE_MS, module.LAUNCH_CHROME) == (9222, 500, True)


def test_accept_key_rfc6455_vector(mw):
    # RFC 6455 §1.3's worked example.
    assert mw.accept_key_for("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def _roundtrip(mw, payload: bytes, opcode: int):
    frame = mw.encode_frame(payload, opcode)
    buf = bytearray(frame)

    def recv_exact(n):
        out = bytes(buf[:n])
        del buf[:n]
        assert len(out) == n
        return out

    reader = mw.FrameReader(recv_exact)
    got_op, fin, got_payload = reader.read_frame()
    assert fin
    return got_op, got_payload


def test_frame_roundtrip_small(mw):
    op, payload = _roundtrip(mw, b"hello", mw.OP_TEXT)
    assert (op, payload) == (mw.OP_TEXT, b"hello")


def test_frame_roundtrip_16bit_and_64bit_lengths(mw):
    for size in (200, 70_000):  # 126..65535 → 16-bit; beyond → 64-bit
        op, payload = _roundtrip(mw, b"x" * size, mw.OP_BINARY)
        assert op == mw.OP_BINARY
        assert payload == b"x" * size


def test_fragmented_message_reassembles_and_answers_ping(mw):
    frames = (
        mw.encode_frame(b"he", mw.OP_TEXT, fin=False)
        + mw.encode_frame(b"", mw.OP_PING)
        + mw.encode_frame(b"llo", mw.OP_CONT)
    )
    buf = bytearray(frames)

    def recv_exact(n):
        out = bytes(buf[:n])
        del buf[:n]
        return out

    pongs = []
    reader = mw.FrameReader(recv_exact)
    opcode, payload = reader.read_message(pongs.append)
    assert (opcode, payload) == (mw.OP_TEXT, b"hello")
    assert pongs == [b""]


def test_the_conversion_is_no_longer_this_fetcher_s_job(mw):
    """W-86 P8: `fetch()` returns bytes and a content type; `fux.decode` converts.

    Asserting the functions are **absent** is the point. A test that they still
    behave correctly would keep passing after someone re-added a private copy,
    which is the exact defect the lift removed.
    """
    assert not hasattr(mw, "html_to_markdown")
    assert not hasattr(mw, "extract_title")
    assert not hasattr(mw, "_MdParser")


def test_link_extraction_stays_here_because_crawling_is_a_fetcher_s_job(mw):
    """The decoder plane may not open a socket, so following links cannot live
    there. This is the one HTML-reading function that correctly belongs to a
    fetcher.
    """
    html = '<body><a href="/x#frag">x</a><a href="mailto:a@b">m</a></body>'
    assert mw.extract_links(html, "https://s.test/base/") == ["https://s.test/x"]


def test_fetch_returns_bytes_and_a_declared_type(mw, monkeypatch):
    """A browser capture has no server header to read, which is exactly why the
    type is stated explicitly rather than left for fux to guess.
    """

    class _Session:
        def capture(self, url):
            return "<h1>Rendered</h1>"

    monkeypatch.setattr(mw, "_session", _Session())
    raw, content_type = mw.fetch("https://s.test/page")
    assert raw == b"<h1>Rendered</h1>"
    assert content_type.startswith("text/html")
