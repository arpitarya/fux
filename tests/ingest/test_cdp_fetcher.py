"""The shipped `cdp.py` fetcher — offline unit tests only.

The file ships in the wheel as **package data** (`src/fux/templates/cdp.py.txt`)
and `fux setup` copies it into the consumer's `.fux/fetchers/cdp.py`, where it
becomes their code (ADR-CDP-FETCHER decision 7). It is never imported by fux —
which is why the extension is one Python's import machinery cannot resolve, and
why these tests have to load it explicitly.

They exercise the pure parts (RFC 6455 framing, handshake key, link
extraction, the contract surface, the `configure` hook) plus the CDP
conversation itself against a **scripted fake peer**. Nothing here opens a
socket or needs Chrome.

⚠ **The interception tests are not incidental.** W-98 Phase 1 replaced a
rendering fetcher with one that pauses a response and reads its body, and two
of its failure modes are silent: a CDP event lost because a command reply was
in flight, and a paused request nobody resolves — which wedges the page until
the timeout rather than raising. Both are asserted below.
"""

from __future__ import annotations

import base64
import importlib.util
import json
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
    module.configure({"cdp_port": 9333, "launch_chrome": True})
    assert module.CDP_PORT == 9333
    assert module.LAUNCH_CHROME is True
    assert module.LOAD_TIMEOUT_S == 30.0  # untouched keys keep their default


def test_launch_chrome_defaults_to_false_because_a_launched_chrome_is_signed_in_to_nothing(mw):
    """The default is the feature. This fetcher exists to borrow a session; a
    browser it launched has none, so every URL worth a browser would come back
    as a login page."""
    assert mw.LAUNCH_CHROME is False


def test_a_retired_config_key_says_so_rather_than_reading_as_a_typo(mw):
    """`settle_ms` configured a render-settle wait that no longer exists. The
    generic unknown-key error would send a reader hunting for a misspelling."""
    with pytest.raises(mw.FetcherError) as caught:
        mw.configure({"settle_ms": 500})
    assert "retired" in str(caught.value)
    assert "load_timeout_s" in str(caught.value)


def test_configure_rejects_an_unknown_key():
    module = _load()
    with pytest.raises(module.FetcherError, match="unknown key"):
        module.configure({"cdp_prot": 9333})


def test_configure_with_an_empty_table_changes_nothing():
    module = _load()
    module.configure({})
    assert (module.CDP_PORT, module.LOAD_TIMEOUT_S, module.LAUNCH_CHROME) == (9222, 30.0, False)


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


# ====================================================================
# Interception — the CDP conversation, against a scripted peer.
# ====================================================================

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class FakeChrome:
    """A scripted CDP peer over the `send_text`/`recv_text`/`close` surface.

    `events` is a list of `(after_method, message)`. Each fires **before** the
    reply to that command — which is the ordering that broke the old `_call`,
    and the reason this fake exists rather than a simple queue.
    """

    def __init__(self, events=None, bodies=None):
        self.sent = []
        self.out = []
        self.events = list(events or [])
        self.bodies = dict(bodies or {})

    def send_text(self, text):
        message = json.loads(text)
        self.sent.append(message)
        method = message["method"]
        while self.events and self.events[0][0] == method:
            self.out.append(self.events.pop(0)[1])
        result = {}
        if method == "Fetch.getResponseBody":
            result = self.bodies[message["params"]["requestId"]]
        self.out.append({"id": message["id"], "result": result})

    def recv_text(self):
        if not self.out:
            raise OSError("scripted peer ran out of messages")
        return json.dumps(self.out.pop(0))

    def close(self):
        pass

    def methods(self):
        return [m["method"] for m in self.sent]

    def params_for(self, method):
        return [m["params"] for m in self.sent if m["method"] == method]


def _paused(request_id, url, status=200, headers=(), resource_type="Document"):
    return {
        "method": "Fetch.requestPaused",
        "params": {
            "requestId": request_id,
            "request": {"url": url},
            "resourceType": resource_type,
            "responseStatusCode": status,
            "responseHeaders": [{"name": n, "value": v} for n, v in headers],
        },
    }


def _body(payload: bytes):
    return {"body": base64.b64encode(payload).decode("ascii"), "base64Encoded": True}


def _session_on(mw, monkeypatch, peer):
    """A CdpSession wired to `peer`, with Chrome discovery stubbed out.

    ⚠ It is `_own_target` that is stubbed, not the retired `_page_target`
    (W-105). The distinction is the point of that change: `_own_target` opens
    and remembers **this thread's** tab, so stubbing it here also asserts, by
    construction, that `fetch_resource` asks for a per-thread target rather
    than reaching for the first one Chrome happens to have.
    """
    session = mw.CdpSession()
    monkeypatch.setattr(session, "ensure_chrome", lambda: None)
    monkeypatch.setattr(session, "_own_target", lambda: {"webSocketDebuggerUrl": "ws://x/y"})
    monkeypatch.setattr(mw, "WebSocket", lambda url, timeout=None: peer)
    return session


def test_the_event_pump_keeps_an_event_that_arrives_while_a_reply_is_pending(mw, monkeypatch):
    """⚠ THE REGRESSION THIS FILE EXISTS FOR.

    `Fetch.requestPaused` fires before `Page.navigate`'s reply. The old `_call`
    read messages and discarded every one whose id did not match, so the event
    was gone — and a paused request nobody resolves wedges the page until the
    timeout, which reads as "the site is slow" rather than as a bug.
    """
    peer = FakeChrome(
        events=[("Page.navigate", _paused("R1", "https://s.test/book.xlsx",
                                          headers=[("Content-Type", _XLSX)]))],
        bodies={"R1": _body(b"PK\x03\x04payload")},
    )
    session = _session_on(mw, monkeypatch, peer)
    resource = session.fetch_resource("https://s.test/book.xlsx")
    assert resource.body == b"PK\x03\x04payload"
    assert resource.content_type == _XLSX
    assert resource.status == 200


def test_every_paused_request_is_resolved_exactly_once(mw, monkeypatch):
    """The invariant is *resolved*, not *how*. A subresource is continued; the
    document we captured is aborted, because we hold the bytes already and
    letting it complete either renders a page or writes a download to disk."""
    peer = FakeChrome(
        events=[
            ("Page.navigate", _paused("SUB", "https://s.test/app.js", resource_type="Script")),
            ("Fetch.continueRequest", _paused("DOC", "https://s.test/d", headers=[("content-type", "text/html")])),
        ],
        bodies={"DOC": _body(b"<html></html>")},
    )
    session = _session_on(mw, monkeypatch, peer)
    session.fetch_resource("https://s.test/d")
    continued = [p["requestId"] for p in peer.params_for("Fetch.continueRequest")]
    failed = [p["requestId"] for p in peer.params_for("Fetch.failRequest")]
    assert continued == ["SUB"]
    assert failed == ["DOC"]
    assert sorted(continued + failed) == ["DOC", "SUB"]  # each exactly once


def test_a_redirect_hop_is_continued_and_the_landing_response_is_captured(mw, monkeypatch):
    """A download URL 30x-es to a CDN on another host. Each hop is its own
    paused request, which is why the urlPattern is `*` and not the target."""
    peer = FakeChrome(
        events=[
            ("Page.navigate", _paused("H1", "https://s.test/dl", status=302)),
            ("Fetch.continueRequest", _paused("H2", "https://cdn.other/blob", status=200,
                                              headers=[("content-type", _XLSX), ("ETag", '"v7"')])),
        ],
        bodies={"H2": _body(b"PK\x03\x04")},
    )
    session = _session_on(mw, monkeypatch, peer)
    resource = session.fetch_resource("https://s.test/dl")
    assert resource.final_url == "https://cdn.other/blob"
    assert resource.url == "https://s.test/dl"      # what we asked for, kept
    assert resource.etag == '"v7"'
    assert [p["requestId"] for p in peer.params_for("Fetch.continueRequest")] == ["H1"]


def test_the_pattern_is_star_and_interception_is_at_the_response_stage(mw, monkeypatch):
    """Narrowing the pattern to the target URL stops matching at the first
    redirect and the fetch hangs. Asserted so a future tidy-up cannot 'fix' it."""
    peer = FakeChrome(
        events=[("Page.navigate", _paused("R", "https://s.test/x", headers=[("content-type", "text/plain")]))],
        bodies={"R": _body(b"hi")},
    )
    session = _session_on(mw, monkeypatch, peer)
    session.fetch_resource("https://s.test/x")
    (pattern,) = peer.params_for("Fetch.enable")[0]["patterns"]
    assert pattern == {"urlPattern": "*", "requestStage": "Response"}


def test_navigate_is_not_awaited_because_it_cannot_return_while_paused(mw, monkeypatch):
    """`Page.navigate` commits only after the response, and we hold the
    response paused — awaiting its reply deadlocks until LOAD_TIMEOUT_S. The
    reply is filed and discarded instead."""
    peer = FakeChrome(
        events=[("Page.navigate", _paused("R", "https://s.test/x", headers=[("content-type", "text/plain")]))],
        bodies={"R": _body(b"hi")},
    )
    session = _session_on(mw, monkeypatch, peer)
    session.fetch_resource("https://s.test/x")
    assert peer.methods().index("Page.navigate") < peer.methods().index("Fetch.getResponseBody")


def test_a_redirect_loop_raises_rather_than_spinning(mw, monkeypatch):
    monkeypatch.setattr(mw, "MAX_REDIRECTS", 2)
    hops = [("Page.navigate", _paused("A", "https://s.test/a", status=302))]
    hops += [("Fetch.continueRequest", _paused(f"H{i}", "https://s.test/b", status=302)) for i in range(6)]
    session = _session_on(mw, monkeypatch, FakeChrome(events=hops))
    with pytest.raises(mw.FetcherError) as caught:
        session.fetch_resource("https://s.test/a")
    assert "redirect" in str(caught.value)


def test_headers_are_read_case_insensitively(mw):
    """CDP hands back whatever casing the server sent. `ETag` and `etag` are
    the same header, and a miss here silently disables `validate()`."""
    assert mw._headers([{"name": "ETag", "value": '"a"'}]) == {"etag": '"a"'}


def test_fetch_returns_the_servers_bytes_and_the_servers_type(mw, monkeypatch):
    """W-98: the bytes are the resource, not a rendering of it, and the type is
    the server's header rather than a guess from the extension."""

    class _Session:
        def fetch_resource(self, url, want_body=True):
            return mw.Resource(url, url, 200, _XLSX, '"e1"', b"PK\x03\x04sheet")

    monkeypatch.setattr(mw, "_session", _Session())
    raw, content_type = mw.fetch("https://s.test/book.xlsx")
    assert raw == b"PK\x03\x04sheet"
    assert content_type == _XLSX


def test_fetch_raises_on_an_empty_body_and_names_where_it_landed(mw, monkeypatch):
    """"Landed somewhere else" is the login-page signature, so the message
    carries the final URL — fux records it as the skip reason verbatim."""

    class _Session:
        def fetch_resource(self, url, want_body=True):
            return mw.Resource(url, "https://login.test/", 200, "text/html", "", b"")

    monkeypatch.setattr(mw, "_session", _Session())
    with pytest.raises(mw.FetcherError) as caught:
        mw.fetch("https://s.test/book.xlsx")
    assert "login.test" in str(caught.value)


def test_validate_returns_the_etag_and_asks_for_no_body(mw, monkeypatch):
    seen = {}

    class _Session:
        def fetch_resource(self, url, want_body=True):
            seen["want_body"] = want_body
            return mw.Resource(url, url, 200, "text/html", '"v9"', b"")

    monkeypatch.setattr(mw, "_session", _Session())
    assert mw.validate("https://s.test/x") == '"v9"'
    assert seen["want_body"] is False


@pytest.mark.parametrize("outcome", ["no-etag", "raises"])
def test_validate_degrades_to_none_which_means_fetch_it(mw, monkeypatch, outcome):
    """None is "I cannot tell", never "unchanged". Fux then fetches and still
    compares the sanitized sha, so `validate` can only ever save work."""

    class _Session:
        def fetch_resource(self, url, want_body=True):
            if outcome == "raises":
                raise mw.FetcherError("no chrome")
            return mw.Resource(url, url, 200, "text/html", "", b"")

    monkeypatch.setattr(mw, "_session", _Session())
    assert mw.validate("https://s.test/x") is None


def test_validate_is_on_the_contract_surface(mw):
    assert callable(mw.validate)


def test_nothing_here_renders_a_page_any_more(mw):
    """Asserting ABSENCE: a test that `capture()` still worked would keep
    passing if someone re-added it, which is the defect the removal fixed. The
    implementation is kept at `archive/templates/cdp-rendering.py.txt`."""
    assert not hasattr(mw, "capture")
    assert not hasattr(mw.CdpSession, "capture")
    assert not hasattr(mw, "SETTLE_MS")
