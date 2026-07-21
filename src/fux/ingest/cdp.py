"""Minimal Chrome DevTools Protocol client — rendered-DOM capture.

Drives the user's *existing* Chrome/Chromium (never bundled) over CDP:
discover/launch → open the page target's WebSocket → `Page.navigate` → wait
for `Page.loadEventFired` (timeout) → settle delay → `Runtime.evaluate`
(`document.documentElement.outerHTML`). Opt-in per source (`render = "cdp"`),
never a silent fallback of plain fetch. The transport is the hand-rolled
RFC 6455 client (ws.py); the `websocket-client` extra is a flagged fallback if
the hand-rolled path fails.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
from ..config import WebParams
from ..errors import FuxError

_CHROME_CANDIDATES = (
    "google-chrome",
    "chromium",
    "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)
_LOAD_TIMEOUT_S = 30.0


def make_renderer(web: WebParams):
    """Returns renderer(url, fallback_html) -> rendered html, for web.crawl()."""
    session = _CdpSession(web)

    def renderer(url: str, fallback_html: str) -> str:
        return session.capture(url)

    return renderer


class _CdpSession:
    def __init__(self, web: WebParams):
        self.web = web
        self.chrome: subprocess.Popen | None = None
        self._msg_id = 0

    # -- chrome discovery/launch ------------------------------------------

    def _endpoint(self) -> str:
        return f"http://127.0.0.1:{self.web.cdp_port}"

    def _targets(self) -> list[dict]:
        with urllib.request.urlopen(f"{self._endpoint()}/json", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _ensure_chrome(self) -> None:
        try:
            self._targets()
            return  # something already listens on the port
        except Exception:
            pass
        binary = next((c for c in _CHROME_CANDIDATES if shutil.which(c) or _is_file(c)), None)
        if binary is None:
            raise FuxError(
                "CDP rendering needs Chrome/Chromium. Install Chrome, or start it "
                f"yourself: chrome --headless --remote-debugging-port={self.web.cdp_port}"
            )
        self.chrome = subprocess.Popen(
            [
                binary,
                "--headless=new",
                f"--remote-debugging-port={self.web.cdp_port}",
                "--no-first-run",
                "--no-default-browser-check",
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
        raise FuxError(
            f"Chrome did not open the CDP port {self.web.cdp_port} within 15s — "
            "is the port in use? Set [sources.web] cdp_port to a free port."
        )

    # -- capture -----------------------------------------------------------

    def capture(self, url: str) -> str:
        self._ensure_chrome()
        target = self._page_target()
        ws = self._connect(target["webSocketDebuggerUrl"])
        try:
            self._call(ws, "Page.enable", {})
            self._call(ws, "Page.navigate", {"url": url})
            self._wait_event(ws, "Page.loadEventFired", timeout=_LOAD_TIMEOUT_S, url=url)
            time.sleep(self.web.settle_ms / 1000)
            result = self._call(
                ws,
                "Runtime.evaluate",
                {"expression": "document.documentElement.outerHTML", "returnByValue": True},
            )
            html = result.get("result", {}).get("value", "")
            if not isinstance(html, str) or not html:
                raise FuxError(f"CDP returned no DOM for {url}")
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

    def _connect(self, ws_url: str):
        from .ws import WebSocket

        try:
            return _HandRolled(WebSocket(ws_url))
        except FuxError:
            raise
        except Exception as exc:
            try:  # flagged fallback: the optional websocket-client extra
                import websocket  # type: ignore

                print(f"fux: hand-rolled WebSocket failed ({exc}); using websocket-client extra")
                return _WsClientFallback(websocket.create_connection(ws_url, timeout=30))
            except ImportError:
                raise FuxError(f"CDP WebSocket connection failed: {exc}") from exc

    # -- protocol ----------------------------------------------------------

    def _call(self, ws, method: str, params: dict) -> dict:
        self._msg_id += 1
        msg_id = self._msg_id
        ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
        deadline = time.monotonic() + _LOAD_TIMEOUT_S
        while time.monotonic() < deadline:
            message = json.loads(ws.recv())
            if message.get("id") == msg_id:
                if "error" in message:
                    raise FuxError(f"CDP {method} failed: {message['error'].get('message')}")
                return message.get("result", {})
        raise FuxError(f"CDP {method}: no response within {_LOAD_TIMEOUT_S}s")

    def _wait_event(self, ws, event: str, timeout: float, url: str) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = json.loads(ws.recv())
            if message.get("method") == event:
                return
        raise FuxError(
            f"page never fired {event} for {url} within {timeout:.0f}s — "
            "the site may block headless Chrome, or needs a longer timeout"
        )

    def close(self) -> None:
        if self.chrome is not None:
            self.chrome.terminate()
            self.chrome = None


class _HandRolled:
    def __init__(self, ws):
        self.ws = ws

    def send(self, text: str) -> None:
        self.ws.send_text(text)

    def recv(self) -> str:
        return self.ws.recv_text()

    def close(self) -> None:
        self.ws.close()


class _WsClientFallback:
    def __init__(self, conn):
        self.conn = conn

    def send(self, text: str) -> None:
        self.conn.send(text)

    def recv(self) -> str:
        return self.conn.recv()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


def _is_file(path: str) -> bool:
    from pathlib import Path

    return Path(path).is_file()
