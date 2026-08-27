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

This default implementation drives your *existing* Chrome/Chromium (never a
bundled browser) over CDP: discover or launch → open the page target's
WebSocket → `Page.navigate` → wait for `Page.loadEventFired` → settle →
`Runtime.evaluate` (rendered `outerHTML`) → deterministic HTML→markdown.
The WebSocket client is hand-rolled RFC 6455 on stdlib `socket` — ported
from the archived v0.26 engine (`archive/v0.26/src/fux/ingest/ws.py` /
`cdp.py` / `htmlmd.py`), which shipped and dogfooded this exact path.

Start Chrome yourself if you prefer (then set LAUNCH_CHROME = False):

    chrome --headless=new --remote-debugging-port=9222
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
from urllib.parse import urljoin, urlsplit

# ============= CONFIG — defaults; [sources.url.config] wins =============
# Each name below maps to a snake_case key in fux.toml's
# `[sources.url.config]` table (see `configure` at the bottom of this file).

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
LAUNCH_CHROME = True  # False: never launch; require a Chrome already listening
CHROME_BINARIES = (
    "google-chrome",
    "chromium",
    "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)
EXTRA_CHROME_FLAGS: tuple[str, ...] = ()  # e.g. ("--proxy-server=…",)
LOAD_TIMEOUT_S = 30.0  # max wait for Page.loadEventFired per URL
SETTLE_MS = 500  # extra wait after load for JS-heavy pages

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
# CDP session — discover/launch Chrome, drive one page target per fetch.
# ====================================================================


class CdpSession:
    def __init__(self) -> None:
        self.chrome: subprocess.Popen | None = None
        self._msg_id = 0

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
                f"start Chrome yourself: chrome --headless=new --remote-debugging-port={CDP_PORT}"
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

    # -- capture -----------------------------------------------------------

    def capture(self, url: str) -> str:
        """Rendered outerHTML for one URL."""
        self.ensure_chrome()
        target = self._page_target()
        ws = WebSocket(target["webSocketDebuggerUrl"])
        try:
            self._call(ws, "Page.enable", {})
            self._call(ws, "Page.navigate", {"url": url})
            self._wait_event(ws, "Page.loadEventFired", timeout=LOAD_TIMEOUT_S, url=url)
            time.sleep(SETTLE_MS / 1000)
            result = self._call(
                ws,
                "Runtime.evaluate",
                {"expression": "document.documentElement.outerHTML", "returnByValue": True},
            )
            html = result.get("result", {}).get("value", "")
            if not isinstance(html, str) or not html:
                raise FetcherError(f"CDP returned no DOM for {url}")
            return html
        finally:
            ws.close()

    def _page_target(self) -> dict:
        for target in self._targets():
            if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                return target
        with urllib.request.urlopen(
            urllib.request.Request(f"{self._endpoint()}/json/new", method="PUT"), timeout=5
        ) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # -- protocol ----------------------------------------------------------

    def _call(self, ws: WebSocket, method: str, params: dict) -> dict:
        self._msg_id += 1
        msg_id = self._msg_id
        ws.send_text(json.dumps({"id": msg_id, "method": method, "params": params}))
        deadline = time.monotonic() + LOAD_TIMEOUT_S
        while time.monotonic() < deadline:
            message = json.loads(ws.recv_text())
            if message.get("id") == msg_id:
                if "error" in message:
                    raise FetcherError(f"CDP {method} failed: {message['error'].get('message')}")
                return message.get("result", {})
        raise FetcherError(f"CDP {method}: no response within {LOAD_TIMEOUT_S}s")

    def _wait_event(self, ws: WebSocket, event: str, timeout: float, url: str) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = json.loads(ws.recv_text())
            if message.get("method") == event:
                return
        raise FetcherError(
            f"page never fired {event} for {url} within {timeout:.0f}s — "
            "the site may block headless Chrome, or needs a longer LOAD_TIMEOUT_S"
        )

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
    "settle_ms": ("SETTLE_MS", int),
}


def configure(config: dict) -> None:
    """Called once after import with `[sources.url.config]` from fux.toml.

    Overrides the CONFIG defaults above. An unknown key raises rather than
    being silently ignored — a typo'd tunable that does nothing is the kind
    of failure you find three renders later.
    """
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
    """One URL -> (the rendered HTML as bytes, its content type).

    **W-86 P8: this no longer converts anything.** A browser capture is already
    a decoded string, so the bytes handed back are that string encoded as UTF-8
    and the type is stated rather than guessed — there is no server header to
    read here, which is exactly why saying `text/html` explicitly matters.

    Raise to have fux skip this URL.
    """
    session = _session or CdpSession()
    html = session.capture(url)
    if not html.strip():
        raise FetcherError(f"nothing returned from {url}")
    return html.encode("utf-8"), "text/html; charset=utf-8"


def close() -> None:
    """Called once after the last fetch — kills Chrome only if we launched it."""
    global _session
    if _session is not None:
        _session.shutdown()
        _session = None
