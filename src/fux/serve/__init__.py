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
- 🔴 **No route writes a committed byte.** `GET` only; every other method is 405.
  The X-ray routes (W-220) fill `.fux/runtime/inspect/` — the gitignored cache
  `fux inspect` fills for the same index — and nothing else. The
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
    """GET routes only — `/`, `/ask`, `/graph`, `/health` and the X-ray tabs'
    `/inspect/*` (SR-SERVE decision 4). Every other method is 405.

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
            elif route in _INSPECT_ROUTES:
                getattr(self, _INSPECT_ROUTES[route])(params)
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


    # -- the X-ray tabs (W-220) --------------------------------------------
    #
    # 🔴 **The server calls `fux.inspect` in-process; the browser computes
    # nothing** — SR-SERVE decision 5 as amended. Every number the Documents and
    # Index tabs show is a field of what these handlers return, which is what
    # `fux inspect --json` would print for the same index.

    def _send_json(self, payload) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8") + b"\n"
        self._send(HTTPStatus.OK, body, _JSON)

    def _documents(self, params: dict) -> None:
        """Every document in `.fux/index/REGISTER` — the list, no X-ray."""
        from ..ingest import register

        root = self.server.state.root()
        rows = [
            {"loc": r.loc, "kind": r.kind, "sha": r.sha, "decoder": r.decoder.split("@", 1)[0]}
            for r in sorted(register.read(root).values(), key=lambda r: r.loc)
        ]
        self._send_json({"documents": rows, "count": len(rows)})

    def _document(self, params: dict) -> None:
        """ONE document's X-ray, computed on the click and cached (pass A)."""
        from ..inspect import xray

        loc = _first(params, "loc").strip()
        if not loc:
            self._json_error(HTTPStatus.BAD_REQUEST, "give me a document: /inspect/document?loc=…")
            return
        self._send_json(xray.document(self.server.state.root(), self.server.state.view(), loc))

    def _document_probes(self, params: dict) -> None:
        """This document's own probes — its title and each heading, one `ask` each."""
        from ..inspect import facts as facts_mod, probes as probes_mod

        loc = _first(params, "loc").strip()
        view = self.server.state.view()
        index = next((i for i, d in enumerate(view.docs) if d.loc == loc or d.id == loc), None)
        if index is None:
            self._json_error(HTTPStatus.NOT_FOUND, f"no indexed document at {loc!r}")
            return
        root = self.server.state.root()
        facts = facts_mod.Facts(by_id={view.docs[index].id: facts_mod.load_or_compute_one(root, view, view.docs[index])})
        result = probes_mod.run(root, view, facts, only=[index])
        self._send_json({"probe": result.by_id.get(view.docs[index].id), "queries": result.queries})

    def _index(self, params: dict) -> None:
        """The corpus report WITHOUT probes — the fast lenses, computed on open."""
        # Both sampled halves are skipped here, so the tab's first render is the
        # exhaustive lenses alone; `/inspect/probes` runs self-retrieval and the
        # probes behind it, through one query cache.
        self._send_json(self.server.state.job("index", probe_sample=None, retrieval_sample=None))

    def _probes(self, params: dict) -> None:
        """The corpus report WITH probes: a sample by default, every document on `all=1`."""
        from ..inspect import probes as probes_mod

        every = _first(params, "all") in ("1", "true", "yes")
        sample = 0 if every else probes_mod.DEFAULT_PROBE_SAMPLE
        self._send_json(self.server.state.job("probes-all" if every else "probes", probe_sample=sample))


#: route -> handler method. GET only, like every other route.
_INSPECT_ROUTES = {
    "/inspect/documents": "_documents",
    "/inspect/document": "_document",
    "/inspect/document/probes": "_document_probes",
    "/inspect/index": "_index",
    "/inspect/probes": "_probes",
}


#: How many rows each capped list carries on the Index tab. The CLI's default is
#: 20; a page can scroll, and the full count still travels beside every list.
TRIAGE_ROWS = 200


#: "Whatever `fux inspect` would use" — distinct from `None`, which skips.
_LIBRARY_DEFAULT = object()


class _JobProgress:
    """`fux.progress`'s phase protocol, recorded instead of painted.

    The page shows the slow part as a progress line — *the slow part is visible,
    never silent* (W-220) — and a phase name, a count and a total are all it
    needs. No clock is read: a count is a fact, a duration would be a guess.
    """

    def __init__(self) -> None:
        self.phase_name = ""
        self.done = 0
        self.total = 0

    def phase(self, name: str, total: int, unit: str = ""):
        progress = self

        class _Phase:
            def __enter__(self_inner):
                progress.phase_name, progress.done, progress.total = name, 0, total
                return self_inner

            def update(self_inner, n: int = 1, detail: str = "") -> None:
                progress.done += n

            def __exit__(self_inner, *exc) -> bool:
                return False

        return _Phase()


class _State:
    """What the server keeps between requests: the root, one `IndexView`, the jobs.

    The view is re-read when the committed shards change, so a re-ingest while
    the page is open is picked up on the next click rather than served stale.
    Jobs are keyed by kind and by the shards they read, so reopening a tab on an
    unchanged index returns the finished report and recomputes nothing.
    """

    def __init__(self, root=None) -> None:
        self._lock = threading.Lock()
        self._root = root
        self._view = None
        self._view_key = None
        self._jobs: dict = {}

    def root(self):
        if self._root is None:
            from ..config import find_root

            root = find_root()
            if root is None:
                raise FuxError("not inside a fux repository (no .fux/ found up the tree)")
            self._root = root
        return self._root

    def _shard_key(self):
        from .. import store as store_mod

        return tuple(
            (p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in store_mod.iter_shard_paths(self.root())
        )

    def view(self):
        from ..inspect._scan import read_index_view

        key = self._shard_key()
        with self._lock:
            if self._view is None or key != self._view_key:
                self._view = read_index_view(self.root())
                self._view_key = key
            return self._view

    def job(self, kind: str, *, probe_sample, retrieval_sample=_LIBRARY_DEFAULT):
        view = self.view()
        key = (kind, self._view_key)
        with self._lock:
            job = self._jobs.get(key)
            if job is None:
                job = {"state": "running", "progress": _JobProgress(), "result": None, "error": None}
                self._jobs[key] = job
                threading.Thread(
                    target=self._run, args=(job, view, probe_sample, retrieval_sample), daemon=True
                ).start()
        if job["state"] == "done":
            return {"state": "done", "report": job["result"]}
        if job["state"] == "error":
            return {"state": "error", "error": job["error"]}
        p = job["progress"]
        return {"state": "running", "phase": p.phase_name, "done": p.done, "total": p.total}

    def _run(self, job, view, probe_sample, retrieval_sample) -> None:
        from ..inspect import as_dict, inspect_index
        from ..inspect.lenses import DEFAULT_RETRIEVAL_SAMPLE

        if retrieval_sample is _LIBRARY_DEFAULT:
            retrieval_sample = DEFAULT_RETRIEVAL_SAMPLE

        try:
            # `top=TRIAGE_ROWS`: the page shows the triage fux ordered, and never
            # re-sorts rows itself — an order is the engine's to state.
            report = inspect_index(
                self.root(), probe_sample=probe_sample, retrieval_sample=retrieval_sample,
                progress=job["progress"], view=view, top=TRIAGE_ROWS,
            )
            job["result"] = as_dict(report)
            job["state"] = "done"
        except Exception as exc:  # a tab must say what failed, not hang
            job["error"] = f"{type(exc).__name__}: {exc}"
            job["state"] = "error"



class _Server(ThreadingHTTPServer):
    """`ThreadingHTTPServer` without the reverse-DNS lookup in `server_bind`.

    ⚠ The stdlib sets `server_name = socket.getfqdn(host)` **between bind and
    listen**, so while that lookup stalls the port refuses every connection. On
    GitHub's macOS runners it stalled past the e2e suite's 30 s start-up budget
    (2026-09-23, `3.0.0-alpha.4`'s CI). The address is always `HOST`, so the name
    is known without asking a resolver.
    """

    def server_bind(self) -> None:
        import socketserver

        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port


def make_server(port: int = DEFAULT_PORT, host: str | None = None, root=None) -> ThreadingHTTPServer:
    """A bound server, not yet serving. Separated so a test can take the port.

    `port=0` asks the OS for a free one, which is what `tests/serve/` uses —
    a fixed port in a test suite is a flake waiting for a busy machine. `root`
    pins the repository the X-ray tabs read; by default it is found from the
    working directory on first use, as every other verb finds it.
    """
    server = _Server((_bind_address(host), port), _Handler)
    server.state = _State(root)
    return server


def cmd_serve(args) -> int:
    """Start the explorer and block until Ctrl-C."""
    server = make_server(port=getattr(args, "port", DEFAULT_PORT) or DEFAULT_PORT)
    url = f"http://{HOST}:{server.server_address[1]}/"
    # Flushed: stdout is block-buffered when piped, and a process ended by
    # TerminateProcess (Windows' SIGTERM) never flushes, so the URL was lost.
    print(f"fux serve — {url}", flush=True)
    print("the page renders `fux ask --json --why`; it computes nothing. Ctrl-C to stop.", flush=True)
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
