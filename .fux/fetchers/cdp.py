"""Consumer-owned URL fetcher — Chrome DevTools Protocol, pure stdlib.

**This file belongs to you, not to fux. It is committed to your repo, at
`.fux/fetchers/cdp.py`, and fux will never rewrite it.** Fux writes it once
if it is missing and reads it by path from `fux.toml`
(`[sources.url] fetcher`) under `fux add <URL>` or `fux update`, calls it to
turn each URL into markdown, and indexes the result exactly like a repo file.
Edit anything — port, launch flags, wait strategy, extraction, even the whole
transport (swap in `websockets` or Playwright if you'd rather carry a
dependency; fux never imports those, only this file's entry points).

Living in a dotdir has one consequence worth knowing: linters that skip
hidden directories by default (ruff does) will not lint this file. That is
deliberate — it is your code, not a fux CI target.

The contract fux relies on — keep these names:

    configure(config: dict) -> None  # optional; once after import, before connect()
    connect() -> None        # optional; called once before the first fetch
    fetch(url: str) -> tuple[bytes, str]   # required; bytes + content type
    close() -> None          # optional; called once after the last fetch

`fetch` may raise on failure — fux records the URL as skipped (with the
error as the reason) and, if a previous ingest indexed it, keeps that older
record rather than deleting it. Everything else here is implementation and
yours to change.

`configure` receives `[sources.url.config]` from `fux.toml` **verbatim**; fux
validates only that it is a table and never reads a key inside it. The
constants below are therefore *defaults*, and the table overrides them — put
tunables in `fux.toml` rather than editing this file, and merges stay clean.

    validate(url) -> str | None            # optional; a cheap change token

This default implementation drives your *existing*, *already-signed-in*
Chrome/Chromium (never a bundled browser) over CDP, and it returns **the
resource the server sent**, not a rendering of it:

    discover Chrome -> open the page target's WebSocket
      -> Fetch.enable(requestStage="Response")
      -> Page.navigate(url)                     [fire-and-forget, see below]
      -> Fetch.requestPaused                    (final url, status, headers)
      -> Fetch.getResponseBody                  (base64 body)
      -> Fetch.failRequest / continueRequest    ALWAYS, or the page hangs

**Why interception and not an in-page `fetch()`.** An earlier draft ran
`Runtime.evaluate` with an in-page `fetch(url, {credentials:'include'})`.
That technique cannot do this job, and it was measured rather than argued:

  * CORS and CSP are **page-level**. CDP is browser-internal and neither
    reaches it. The same cross-origin URL sending no `Access-Control-Allow-
    Origin` returned `TypeError: Failed to fetch` in-page and **8557 bytes**
    under interception.
  * A cross-origin in-page fetch exposes only the **CORS-safelisted** response
    headers, so `ETag` is invisible — `validate()` below could never have
    worked. Interception reads every header the server sent.
  * `Content-Disposition: attachment` is intercepted **before** Chrome turns
    it into a download, so no download-directory dance is needed.

A rendered DOM was also the wrong output: it carries nonces, timestamps and
session ids, so its sha changes on every fetch — nondeterministic input to an
engine that asserts byte-identical results.

**Auth is your browser's, borrowed.** This file stores, reads and handles no
credential of any kind. Point it at a Chrome you are already signed in to. If
you are not signed in, the site returns its login page and fux refuses it
rather than indexing it.

`extract_links` is still here and still yours: crawling is a fetcher's job,
because the decoder plane may not open a socket. Nothing in fux calls it — it
is the seam for the crawl you may want to write.

The WebSocket client is hand-rolled RFC 6455 on stdlib `socket` — ported
from the archived v0.26 engine (`archive/v0.26/src/fux/ingest/ws.py`), which
shipped and dogfooded it.

**LAUNCH_CHROME defaults to False**, because a browser this file launched is
signed in to nothing. Start your own and point it at the port:

    chrome --remote-debugging-port=9222
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from html.parser import HTMLParser
from typing import NamedTuple
from urllib.parse import urljoin, urlsplit

# ============= CONFIG — defaults; [sources.url.config] wins =============
# Each name below maps to a snake_case key in fux.toml's
# `[sources.url.config]` table (see `configure` at the bottom of this file).

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
#: **False by default, and that is the whole point of this fetcher.** A Chrome
#: this file launches is signed in to nothing, so every URL worth a browser
#: would come back as a login page. Start your own signed-in Chrome with
#: `--remote-debugging-port` and leave this False. Set it True only for public
#: pages where the session is irrelevant.
LAUNCH_CHROME = False
CHROME_BINARIES = (
    "google-chrome",
    "chromium",
    "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)
EXTRA_CHROME_FLAGS: tuple[str, ...] = ()  # e.g. ("--proxy-server=…",)
LOAD_TIMEOUT_S = 30.0  # max wait for the intercepted response, per URL

#: Redirect chain cap. Each hop is a separate `Fetch.requestPaused`, so an
#: unbounded loop here is an unbounded wait. Not a `fux.toml` key on purpose —
#: see `_SETTINGS` at the bottom for why this file stopped adding them.
MAX_REDIRECTS = 20

# ====================================================================
# RFC 6455 WebSocket client — stdlib socket/hashlib/base64.
# Just enough of the protocol for CDP: masked client frames, text/binary/
# ping/pong/close, fragmentation reassembly, 16/64-bit payload lengths.
# ====================================================================

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


class FetcherError(RuntimeError):
    """Raised for every expected failure; fux records it as the skip reason."""


#: W-82 3.3 -- DECLARED EXPLICITLY, not omitted. Omission and 1 behave
#: identically, and this line is where the REASON gets written for whoever
#: copies this file and starts editing it:
#:
#:   `connect()` sets a module-global `_session` holding ONE WebSocket that
#:   every `fetch()` reuses. Two threads writing frames onto it produce
#:   PLAUSIBLE DOCUMENTS ATTRIBUTED TO THE WRONG URLs -- which lands in the
#:   committed index, passes every determinism check, and is caught only by a
#:   human reading an answer.
#:
#: Raise this only after giving each worker its own session.
MAX_PARALLEL = 1

def accept_key_for(key: str) -> str:
    """Sec-WebSocket-Accept for a Sec-WebSocket-Key (RFC 6455 §4.2.2)."""
    digest = hashlib.sha1((key + _WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def encode_frame(payload: bytes, opcode: int = OP_TEXT, *, mask: bool = True, fin: bool = True) -> bytes:
    """One client frame. Client frames MUST be masked (RFC 6455 §5.3)."""
    head = bytes([(0x80 if fin else 0) | opcode])
    length = len(payload)
    mask_bit = 0x80 if mask else 0
    if length < 126:
        head += bytes([mask_bit | length])
    elif length < 65536:
        head += bytes([mask_bit | 126]) + struct.pack(">H", length)
    else:
        head += bytes([mask_bit | 127]) + struct.pack(">Q", length)
    if not mask:
        return head + payload
    key = os.urandom(4)
    masked = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    return head + key + masked


class FrameReader:
    """Incremental frame decoder over a `recv_exact(n)` callable."""

    def __init__(self, recv_exact):
        self.recv_exact = recv_exact

    def read_frame(self) -> tuple[int, bool, bytes]:
        """Returns (opcode, fin, payload); unmasks if a mask is present."""
        b0, b1 = self.recv_exact(2)
        fin = bool(b0 & 0x80)
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        length = b1 & 0x7F
        if length == 126:
            (length,) = struct.unpack(">H", self.recv_exact(2))
        elif length == 127:
            (length,) = struct.unpack(">Q", self.recv_exact(8))
        key = self.recv_exact(4) if masked else b""
        payload = self.recv_exact(length) if length else b""
        if masked:
            payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
        return opcode, fin, payload

    def read_message(self, pong) -> tuple[int, bytes]:
        """Next complete message: reassembles fragments, answers pings inline."""
        opcode, fin, payload = self.read_frame()
        while opcode in (OP_PING, OP_PONG):
            if opcode == OP_PING:
                pong(payload)
            opcode, fin, payload = self.read_frame()
        message_op = opcode
        parts = [payload]
        while not fin:
            opcode, fin, payload = self.read_frame()
            if opcode == OP_PING:
                pong(payload)
                fin = False
                continue
            parts.append(payload)
        return message_op, b"".join(parts)


class WebSocket:
    """Blocking client socket speaking RFC 6455 — sized for CDP, not generality."""

    def __init__(self, url: str, timeout: float = 30.0):
        parts = urlsplit(url)
        if parts.scheme != "ws":
            raise FetcherError(f"unsupported WebSocket scheme {parts.scheme!r} (CDP uses ws://)")
        self.host = parts.hostname or "127.0.0.1"
        self.port = parts.port or 80
        self.resource = parts.path + (f"?{parts.query}" if parts.query else "") or "/"
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.reader = FrameReader(self._recv_exact)
        self._handshake()

    def _handshake(self) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.resource} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise FetcherError("WebSocket handshake failed: connection closed")
            response += chunk
        head, _, rest = response.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        if "101" not in lines[0]:
            raise FetcherError(f"WebSocket handshake rejected: {lines[0]}")
        headers = {
            k.strip().lower(): v.strip()
            for k, _, v in (line.partition(":") for line in lines[1:])
        }
        if headers.get("sec-websocket-accept") != accept_key_for(key):
            raise FetcherError("WebSocket handshake failed: bad Sec-WebSocket-Accept")
        self._buffer = rest

    def _recv_exact(self, n: int) -> bytes:
        data = self._buffer[:n]
        self._buffer = self._buffer[n:]
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise FetcherError("WebSocket closed mid-frame")
            data += chunk
        return data

    def send_text(self, text: str) -> None:
        self.sock.sendall(encode_frame(text.encode("utf-8"), OP_TEXT))

    def recv_text(self) -> str:
        opcode, payload = self.reader.read_message(self._pong)
        if opcode == OP_CLOSE:
            raise FetcherError("WebSocket closed by peer")
        return payload.decode("utf-8", errors="replace")

    def _pong(self, payload: bytes) -> None:
        self.sock.sendall(encode_frame(payload, OP_PONG))

    def close(self) -> None:
        try:
            self.sock.sendall(encode_frame(b"", OP_CLOSE))
            self.sock.close()
        except OSError:
            pass


# ====================================================================
# HTML -> Markdown lives in `fux.decode.htmldoc` (W-86 P1), imported below.
# It used to be duplicated here and in http.py, with a comment asking the
# two copies to stay identical and nothing checking that they did. Two
# fetchers converting differently would make the committed index depend on
# WHICH ONE RAN, which is L3. Link extraction stays here: crawling is this
# fetcher's job, not the decoder plane's.
# ====================================================================



def extract_links(html: str, base_url: str) -> list[str]:
    """Absolute hrefs, document order, deduped; fragments stripped."""
    parser = _LinkParser(base_url)
    parser.feed(html)
    parser.close()
    return parser.links


class _LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base_url
        self.links: list[str] = []
        self._seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "base" and attrs.get("href"):
            self.base = attrs["href"]
            return
        if tag != "a":
            return
        href = (attrs.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:", "data:")):
            return
        absolute = urljoin(self.base, href).split("#", 1)[0]
        if absolute.startswith(("http://", "https://")) and absolute not in self._seen:
            self._seen.add(absolute)
            self.links.append(absolute)



# ====================================================================
# One intercepted response.
# ====================================================================


class Resource(NamedTuple):
    """What the server sent, as the browser saw it.

    `final_url` is where the request LANDED, which is not `url` whenever a
    redirect ran — and a login page is exactly that case, so fux compares the
    two. `content_type` is the server's header, never a guess from the
    extension: guessing here writes the wrong bytes into the index.
    """

    url: str
    final_url: str
    status: int
    content_type: str
    etag: str
    body: bytes


def _headers(pairs: list[dict]) -> dict[str, str]:
    """CDP's `[{name, value}]` -> a lowercased dict. Last value wins."""
    return {str(h.get("name", "")).lower(): str(h.get("value", "")) for h in pairs}


# ====================================================================
# CDP session — discover/launch Chrome, drive one page target per fetch.
# ====================================================================


class CdpSession:
    def __init__(self) -> None:
        self.chrome: subprocess.Popen | None = None
        self._msg_id = 0
        #: Command replies by id, and events in arrival order. See the event
        #: pump below — these two exist because one queue loses messages.
        self._results: dict[int, dict] = {}
        self._events: list[dict] = []

    # -- chrome discovery/launch ------------------------------------------

    def _endpoint(self) -> str:
        return f"http://{CDP_HOST}:{CDP_PORT}"

    def _targets(self) -> list[dict]:
        with urllib.request.urlopen(f"{self._endpoint()}/json", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def ensure_chrome(self) -> None:
        try:
            self._targets()
            return  # something already listens on the port
        except Exception:
            pass
        if not LAUNCH_CHROME:
            raise FetcherError(
                f"nothing listening on {self._endpoint()} and LAUNCH_CHROME is False — "
                f"start your own signed-in Chrome: chrome --remote-debugging-port={CDP_PORT}\n"
                "That is the default because a browser this file launches is signed in "
                "to nothing, and every URL worth a browser would come back as a login page."
            )
        binary = next((c for c in CHROME_BINARIES if shutil.which(c) or os.path.isfile(c)), None)
        if binary is None:
            raise FetcherError(
                "CDP rendering needs Chrome/Chromium. Install Chrome, or start it "
                f"yourself: chrome --headless=new --remote-debugging-port={CDP_PORT}"
            )
        self.chrome = subprocess.Popen(
            [
                binary,
                "--headless=new",
                f"--remote-debugging-port={CDP_PORT}",
                "--no-first-run",
                "--no-default-browser-check",
                *EXTRA_CHROME_FLAGS,
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                self._targets()
                return
            except Exception:
                time.sleep(0.25)
        raise FetcherError(
            f"Chrome did not open the CDP port {CDP_PORT} within 15s — "
            "is the port in use? Edit CDP_PORT in this file."
        )

    # -- interception ------------------------------------------------------

    def fetch_resource(self, url: str, *, want_body: bool = True) -> "Resource":
        """Navigate to `url` and return the response the server actually sent.

        The bytes come from `Fetch.getResponseBody` on a paused response, never
        from the page. See the module docstring for why that distinction is
        load-bearing rather than stylistic.
        """
        self.ensure_chrome()
        target = self._page_target()
        ws = WebSocket(target["webSocketDebuggerUrl"], timeout=LOAD_TIMEOUT_S)
        self._results.clear()
        self._events.clear()
        try:
            # ⚠ `urlPattern` is "*", not the target URL, and that is DELIBERATE.
            # A download URL typically 30x-es to a CDN on another host, and each
            # hop is its own `Fetch.requestPaused`. A pattern narrowed to the
            # URL we asked for stops matching at the first redirect and the
            # fetch hangs until LOAD_TIMEOUT_S. The cost of "*" is that
            # subresources pause too, which is why EVERY paused request below
            # is continued or failed — an unresolved one wedges the page.
            self._call(ws, "Fetch.enable", {
                "patterns": [{"urlPattern": "*", "requestStage": "Response"}],
            })
            try:
                # Fire-and-forget, and this is not a shortcut. `Page.navigate`
                # does not return until the navigation commits, and it cannot
                # commit while we hold its response paused — awaiting the result
                # here deadlocks until the timeout. The reply lands in
                # `_results` when we resolve the request and is discarded there.
                self._send(ws, "Page.navigate", {"url": url})
                return self._await_document(ws, url, want_body=want_body)
            finally:
                # Best-effort: the socket is about to close anyway, and a
                # failure here must not mask the real exception.
                try:
                    self._call(ws, "Fetch.disable", {})
                except FetcherError:
                    pass
        finally:
            ws.close()

    def _await_document(self, ws: WebSocket, url: str, *, want_body: bool) -> "Resource":
        """Pump paused requests until the main document's response arrives."""
        deadline = time.monotonic() + LOAD_TIMEOUT_S
        for _ in range(MAX_REDIRECTS + 1):
            paused = self._wait_event(ws, "Fetch.requestPaused", deadline, url)
            request_id = paused["requestId"]
            status = int(paused.get("responseStatusCode") or 0)
            is_document = paused.get("resourceType") == "Document"

            if not is_document or 300 <= status < 400:
                # A subresource, or a hop on the way. Let it run; the next
                # `Fetch.requestPaused` is the one we are waiting for.
                self._resolve(ws, request_id, abort=False)
                continue

            headers = _headers(paused.get("responseHeaders") or [])
            body = b""
            try:
                if want_body:
                    result = self._call(ws, "Fetch.getResponseBody", {"requestId": request_id})
                    raw = result.get("body") or ""
                    body = base64.b64decode(raw) if result.get("base64Encoded") else raw.encode("utf-8")
            finally:
                # Abort rather than continue: we already hold the bytes, and
                # letting the navigation complete would either render the page
                # or start a download to disk for an attachment. Either way it
                # is work nobody reads. The request IS resolved — that is the
                # invariant, not which way it resolves.
                self._resolve(ws, request_id, abort=True)

            return Resource(
                url=url,
                final_url=str(paused.get("request", {}).get("url") or url),
                status=status,
                content_type=headers.get("content-type", ""),
                etag=headers.get("etag", ""),
                body=body,
            )

        raise FetcherError(
            f"more than {MAX_REDIRECTS} redirects fetching {url} — a redirect loop, "
            "or a sign-in flow bouncing between an identity provider and the site"
        )

    def _resolve(self, ws: WebSocket, request_id: str, *, abort: bool) -> None:
        """Every paused request gets exactly one of these. Never skip it."""
        method = "Fetch.failRequest" if abort else "Fetch.continueRequest"
        params = {"requestId": request_id}
        if abort:
            params["errorReason"] = "Aborted"
        try:
            self._call(ws, method, params)
        except FetcherError:
            # The request can vanish under us (the page navigated away, the
            # target closed). Nothing is leaked by that, and raising here would
            # replace a real error with a bookkeeping one.
            pass

    def _page_target(self) -> dict:
        for target in self._targets():
            if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                return target
        with urllib.request.urlopen(
            urllib.request.Request(f"{self._endpoint()}/json/new", method="PUT"), timeout=5
        ) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # -- protocol ----------------------------------------------------------
    #
    # ⚠ THE EVENT PUMP, and why the obvious loop was wrong.
    #
    # `_call` used to read messages and DISCARD every one whose id did not
    # match. CDP interleaves events with command replies on the same socket, so
    # a `Fetch.requestPaused` arriving while a command was in flight was thrown
    # away — and a paused request nobody resolves wedges the page until the
    # timeout. `_pump` files each message by kind; `_call` and `_wait_event`
    # both drain the same queues, so neither can lose the other's messages.

    def _pump(self, ws: WebSocket, deadline: float, waiting_for: str) -> None:
        """Read one message off the socket and file it by kind."""
        if time.monotonic() >= deadline:
            raise FetcherError(
                f"CDP: no {waiting_for} within {LOAD_TIMEOUT_S:.0f}s — the site may "
                "block headless Chrome, need a sign-in, or need a longer LOAD_TIMEOUT_S"
            )
        try:
            message = json.loads(ws.recv_text())
        except OSError as exc:
            raise FetcherError(f"CDP connection died waiting for {waiting_for}: {exc}") from exc
        if "id" in message:
            self._results[int(message["id"])] = message
        elif "method" in message:
            self._events.append(message)

    def _send(self, ws: WebSocket, method: str, params: dict) -> int:
        """Dispatch a command without waiting for its reply."""
        self._msg_id += 1
        ws.send_text(json.dumps({"id": self._msg_id, "method": method, "params": params}))
        return self._msg_id

    def _call(self, ws: WebSocket, method: str, params: dict) -> dict:
        msg_id = self._send(ws, method, params)
        deadline = time.monotonic() + LOAD_TIMEOUT_S
        while True:
            if msg_id in self._results:
                message = self._results.pop(msg_id)
                if "error" in message:
                    raise FetcherError(f"CDP {method} failed: {message['error'].get('message')}")
                return message.get("result", {})
            self._pump(ws, deadline, f"a reply to {method}")

    def _wait_event(self, ws: WebSocket, event: str, deadline: float, url: str) -> dict:
        """Next `event`, taking one already queued in preference to reading."""
        while True:
            for index, message in enumerate(self._events):
                if message.get("method") == event:
                    return self._events.pop(index).get("params", {})
            self._pump(ws, deadline, f"{event} for {url}")

    def shutdown(self) -> None:
        if self.chrome is not None:
            self.chrome.terminate()
            self.chrome = None


# ====================================================================
# The entry points fux calls. Keep the names; change the bodies.
# ====================================================================

_session: CdpSession | None = None

# fux.toml key -> (this module's global, coercion). Add your own keys here;
# fux passes the whole table through without looking inside it.
_SETTINGS = {
    "cdp_host": ("CDP_HOST", str),
    "cdp_port": ("CDP_PORT", int),
    "launch_chrome": ("LAUNCH_CHROME", bool),
    "chrome_binaries": ("CHROME_BINARIES", tuple),
    "extra_chrome_flags": ("EXTRA_CHROME_FLAGS", tuple),
    "load_timeout_s": ("LOAD_TIMEOUT_S", float),
}

#: Keys this file used to accept, and what to do instead. They get a specific
#: error rather than falling into the generic unknown-key list, because
#: "unknown key" reads like a typo when the real answer is "that setting no
#: longer describes anything this fetcher does".
_RETIRED = {
    "settle_ms": (
        "there is no render step to settle any more — this fetcher intercepts "
        "the response instead of waiting for JavaScript. Delete the key; raise "
        "load_timeout_s if a slow site is timing out."
    ),
}

#: ⚠ Think twice before adding a key here. `[sources.url.config]` is passed
#: VERBATIM to every fetcher, and `http.py.configure()` raises on keys it does
#: not know — so a new `cdp` tunable in that table breaks a repo that also uses
#: `http.py`. Module constants (MAX_REDIRECTS, MAX_PARALLEL) have no such
#: reach, which is why the ones added here since are constants.


def configure(config: dict) -> None:
    """Called once after import with `[sources.url.config]` from fux.toml.

    Overrides the CONFIG defaults above. An unknown key raises rather than
    being silently ignored — a typo'd tunable that does nothing is the kind
    of failure you find three renders later.
    """
    for key in sorted(set(config) & set(_RETIRED)):
        raise FetcherError(f"[sources.url.config] {key} is retired: {_RETIRED[key]}")
    unknown = sorted(set(config) - set(_SETTINGS))
    if unknown:
        raise FetcherError(
            f"[sources.url.config] unknown key(s): {', '.join(unknown)} — "
            f"known keys: {', '.join(sorted(_SETTINGS))}"
        )
    for key, value in config.items():
        name, coerce = _SETTINGS[key]
        try:
            globals()[name] = coerce(value)
        except (TypeError, ValueError) as exc:
            raise FetcherError(f"[sources.url.config] {key}: {exc}") from exc


def connect() -> None:
    """Called once before the first fetch. Reuses one Chrome for the run."""
    global _session
    _session = CdpSession()
    _session.ensure_chrome()


def fetch(url: str) -> tuple[bytes, str]:
    """One URL -> (the bytes the server sent, its content type).

    **The bytes are the resource, not a rendering of it.** A `.xlsx` comes back
    as a workbook and fux's decoder plane reads it; an HTML page comes back as
    that page's HTML. Nothing here converts anything — `fux.decode` owns that,
    and it owned it before this file changed (W-86 P8).

    Raise to have fux skip this URL and keep any record a previous ingest made.
    """
    session = _session or CdpSession()
    resource = session.fetch_resource(url)
    if not resource.body:
        raise FetcherError(
            f"empty response from {url} (status {resource.status}, "
            f"landed on {resource.final_url})"
        )
    return resource.body, resource.content_type


def validate(url: str) -> str | None:
    """An opaque change token for `url`, or None meaning "I cannot tell".

    Returns the server's `ETag`. **None is always safe** — fux degrades to a
    full fetch, and the sanitized-sha comparison still decides whether any
    shard is written. A token can only ever save work; it can never cause a
    record to change (see `validate_group` in fux's `urlsrc.py`).

    ⚠ **This saves the decode and the shard comparison, NOT the download.**
    Interception happens at `requestStage: "Response"`, so Chrome has already
    transferred the body by the time these headers exist. A header-only check
    would need a HEAD request, which the sites this fetcher exists for
    routinely refuse. Stated plainly here because the opposite is easy to
    assume from the word "validate".
    """
    session = _session or CdpSession()
    try:
        resource = session.fetch_resource(url, want_body=False)
    except FetcherError:
        return None  # cannot tell -> fux fetches, which is the safe direction
    return resource.etag or None


def close() -> None:
    """Called once after the last fetch — kills Chrome only if we launched it."""
    global _session
    if _session is not None:
        _session.shutdown()
        _session = None
