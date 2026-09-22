"""`fux serve` — a local page over the real `ask`, and nothing of its own.

**SR-SERVE.** Arpit's framing, 2026-09-22: *"the way I'm thinking about fux is
something like Google. If a question gets asked, if you have the best 10
documents, the answer the agent gives is going to be mostly correct."* So the
inspection surface is **question-first**: type a question, get the ranked list
with the hood open — which words won, which links helped, how sure fux is, and
the one lever that would change it.

## The whole design is one sentence: the page is a renderer

🔴 **Nothing in the page computes a score, a band or a rank**, and this module is
what makes that possible. A browser cannot hold a corpus's postings and stay
honest — the three-document sample built while this was being designed already
embedded 96 KB of stems — and re-implementing BM25F, the walk and the band in JS
would be a **restatement in the [L0](../../../records/0002_LAW-0-authority.md)
sense**: two rankers that could disagree while both looking correct.

So `/ask` answers with **exactly what `fux ask --json --why` prints**, and it
gets those bytes the only way that claim can be true — by running that command,
in this process, and handing back its stdout. Not *the same code path*; **the
same command**. `tests/serve/test_routes.py` compares the two byte for byte, and
that test is cheap only because this module refused to build a second payload.

⚠ **The cost is honest and small**: an argparse parse and an output-config read
per request, on a localhost tool a person types into. The alternative buys
microseconds and sells the one property the page exists to have.

## The fences

- 🔴 **`127.0.0.1` and nothing else.** `--host` does not exist; a bind address
  is not a knob. [L4](../../../records/0006_LAW-4-offline-by-default.md) is
  offline-by-default and a page served on `0.0.0.0` is a corpus's vocabulary
  offered to the network. `_bind_address` is a function so the refusal has a
  name and a test.
- 🔴 **No route writes anything.** `GET` only; every other method is 405. The
  server keeps no log of its own — [L8](../../../records/0001_LAWS.md) decision 8
  puts every durable trace of use on a gitignored path, and the one that exists
  is the provenance journal, which is opt-in and is not this.
- 🔴 **The page is one file with no external host.** Inline CSS and JS, no CDN,
  no font fetch: it must render with the network unplugged, which is the same
  law and also simply what an offline tool owes.
- **Stdlib only** ([L1](../../../records/0003_LAW-1-zero-cost.md)). `http.server`
  is enough for one person on one machine, and the law permits a dependency but
  a record still has to decide one. None is needed here.

## What this module deliberately does NOT do

No *apply this lever* button, no editing, no write route. Every lever the page
prints is a committed change made by a person or by a session that was asked;
**the page proposes and never acts.** That is the same discipline
`fux inspect` carries, and it is why the skill beside this verb says *never
apply a lever it printed unasked*.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..errors import FuxError

#: The only address this server binds. **Not a flag.** See the module docstring.
HOST = "127.0.0.1"

#: Default port. Arbitrary and high, chosen so it collides with nothing common;
#: `--port` moves it.
DEFAULT_PORT = 7337

#: The single bundled page. `L10` — what a consumer is served is build output,
#: and for one self-contained HTML file the authored form and the built form are
#: the same bytes. There is nothing to bundle and nothing to minify.
PAGE = Path(__file__).resolve().parent / "page.html"

_JSON = "application/json; charset=utf-8"
_HTML = "text/html; charset=utf-8"


def _bind_address(host: str | None) -> str:
    """The address to bind, or raise. **`127.0.0.1` is the contract.**

    A function rather than a constant used inline, so that *"this server refuses
    to be reachable"* is a thing a test can call and a reader can find. A caller
    that passes anything else is not configuring a tool, it is asking for a
    different tool.
    """
    if host in (None, "", HOST, "localhost"):
        return HOST
    raise FuxError(
        f"fux serve binds {HOST} and nothing else (asked for {host!r}). "
        "The page shows a corpus's vocabulary, its passages and the questions "
        "somebody typed; serving that off-machine is not a flag fux has."
    )


def _run_cli(argv: list[str]) -> tuple[int, str]:
    """Run a fux command in this process and capture its stdout.

    🔴 **This is the whole reason `/ask` can promise byte-equality with the
    CLI.** A second payload builder would be a second contract, free to drift a
    key at a time with nothing to notice; running the command means the two
    cannot differ, because they are one thing.

    stderr is **not** captured and not forwarded: `--why`'s human block, the
    archived-results note and the progress plane all live there by design
    (`query/__init__.py::_declare_derivation`), and the page reads `--json`.
    Letting it through to the terminal is also how a person running `fux serve`
    sees what their page is doing.
    """
    from .. import cli

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            code = cli.main(argv)
        except SystemExit as exc:  # argparse's usage errors exit rather than return
            code = int(exc.code or 0)
    return code, buf.getvalue()


def _first(params: dict, key: str) -> str:
    values = params.get(key) or []
    return values[0] if values else ""


class _Handler(BaseHTTPRequestHandler):
    """Four GET routes and no verbs. Every other method is 405.

    ⚠ **`log_message` is silenced deliberately.** `BaseHTTPRequestHandler`
    writes an access line per request naming the full query string — which is
    the question somebody typed. That is a use record, and
    [L8](../../../records/0001_LAWS.md) decision 8 says every durable trace of
    use lives on a gitignored path; a line on the operator's terminal is not
    durable, but it is also not something this verb was asked to print, and the
    provenance journal is the surface that exists for it.
    """

    server_version = "fux-serve"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # noqa: A002 - stdlib signature
        return

    # -- plumbing ---------------------------------------------------------

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # The page is served to one browser on one machine and embeds
        # everything it needs; nothing here may be fetched from anywhere else.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status: int, message: str) -> None:
        self._send(status, json.dumps({"error": message}).encode("utf-8") + b"\n", _JSON)

    # -- routes -----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - stdlib signature
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)
        try:
            if route == "/":
                self._page()
            elif route == "/ask":
                self._ask(params)
            elif route == "/graph":
                self._graph(params)
            elif route == "/health":
                self._health()
            else:
                self._json_error(HTTPStatus.NOT_FOUND, f"no route {route}")
        except FuxError as exc:
            self._json_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - a local tool must not 500 silently
            self._json_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"{type(exc).__name__}: {exc}")

    def do_POST(self) -> None:  # noqa: N802 - stdlib signature
        """🔴 **No route writes anything**, and the refusal is explicit.

        A 405 with a reason is what tells the next person that read-only is a
        decision rather than an omission — the page proposes levers and never
        applies one.
        """
        self._json_error(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "fux serve is read-only: it proposes levers and applies none. "
            "Every change is a committed edit made by a person.",
        )

    do_PUT = do_DELETE = do_PATCH = do_POST

    def _page(self) -> None:
        try:
            body = PAGE.read_bytes()
        except OSError as exc:
            self._json_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"page.html is missing: {exc}")
            return
        self._send(HTTPStatus.OK, body, _HTML)

    def _ask(self, params: dict) -> None:
        query = _first(params, "q").strip()
        if not query:
            self._json_error(HTTPStatus.BAD_REQUEST, "give me a question: /ask?q=…")
            return
        argv = ["ask", query, "--json", "--why", "--band"]
        top = _first(params, "top").strip()
        if top:
            if not top.isdigit() or int(top) < 1:
                self._json_error(HTTPStatus.BAD_REQUEST, f"top must be a positive integer, not {top!r}")
                return
            argv += ["--top", top]
        code, out = _run_cli(argv)
        if not out.strip():
            self._json_error(HTTPStatus.BAD_REQUEST, f"fux ask exited {code} and printed nothing")
            return
        self._send(HTTPStatus.OK, out.encode("utf-8"), _JSON)

    def _graph(self, params: dict) -> None:
        seeds = [s for s in (params.get("seed") or []) if s.strip()]
        if not seeds:
            self._json_error(HTTPStatus.BAD_REQUEST, "give me at least one --seed: /graph?seed=…")
            return
        argv = ["graph", "--json"]
        for seed in seeds:
            argv += ["--seed", seed]
        code, out = _run_cli(argv)
        if not out.strip():
            self._json_error(HTTPStatus.BAD_REQUEST, f"fux graph exited {code} and printed nothing")
            return
        self._send(HTTPStatus.OK, out.encode("utf-8"), _JSON)

    def _health(self) -> None:
        """Version and the index's schema id — the two things a page must not guess.

        The page shows a footer saying which engine and which index it is
        looking at. Deriving that in JS would mean parsing a shard header in the
        browser; reading it here is one line.
        """
        from .. import __version__
        from ..store.format import ANALYZER_VERSION, SCHEMA_ID

        payload = {
            "version": __version__,
            "schema": SCHEMA_ID,
            "analyzer": ANALYZER_VERSION,
            "host": HOST,
        }
        self._send(HTTPStatus.OK, json.dumps(payload).encode("utf-8") + b"\n", _JSON)


def make_server(port: int = DEFAULT_PORT, host: str | None = None) -> ThreadingHTTPServer:
    """A bound server, not yet serving. Separated so a test can take the port.

    `port=0` asks the OS for a free one, which is what `tests/serve/` uses —
    a fixed port in a test suite is a flake waiting for a busy machine.
    """
    return ThreadingHTTPServer((_bind_address(host), port), _Handler)


def cmd_serve(args) -> int:
    """Start the explorer and block until Ctrl-C."""
    server = make_server(port=getattr(args, "port", DEFAULT_PORT) or DEFAULT_PORT)
    url = f"http://{HOST}:{server.server_address[1]}/"
    print(f"fux serve — {url}")
    print("the page renders `fux ask --json --why`; it computes nothing. Ctrl-C to stop.")
    if getattr(args, "open", False):
        # In a thread, because a browser launcher can block for seconds and the
        # server should already be answering when the tab arrives.
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("", file=sys.stderr)
    finally:
        server.server_close()
    return 0
