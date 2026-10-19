"""`fux lsp` — a stdio Language Server over the committed index. W-285.

**Why this exists.** `fux mcp` hands the index to an agent; nothing handed it
to the person editing the documents. The index already knows which documents
exist, what links to what, and what is archived or superseded — and the editor
showed none of it. LSP is the one protocol every editor speaks, so the server
is written once and VS Code, Neovim, Helix, Zed and JetBrains all reach it
([SR-LSP](../../records/0163_lsp.md)).

**Four features, mapped onto what the index already holds** — nothing here
ranks differently from `fux ask` or walks differently from `fux_related`:

| LSP method | what fux answers |
|---|---|
| `workspace/symbol` | the query ranked by `run_query`, each hit a symbol at its best-matching heading |
| `textDocument/hover` | on a link: the target's title, archived/superseded state, date and link counts |
| `textDocument/references` | the documents that link to this one — backlinks, at the link's own line |
| `textDocument/publishDiagnostics` | a warning on every link to an archived or superseded document |

**Stdlib only**, like `mcp.py` and for its reason (SR-MCP decision 1): the base
protocol is a `Content-Length` header and a JSON body, which is `json` and a
byte stream. **The index is resident** through the same `store.resident.Holder`
`fux mcp` uses, re-keyed before every request, so an ingest is seen by the next
request without a restart.

**Positions are UTF-16 code units** — LSP's default encoding, and the only one
every client accepts. A column is computed on the line's UTF-16 encoding, never
on Python's code points, or a link after an emoji lands one column late.
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from .constants import fixed
from .errors import FuxError

_JSONRPC = fixed("mcp", "jsonrpc")
_PARSE_ERROR = fixed("mcp", "parse_error")
_METHOD_NOT_FOUND = fixed("mcp", "method_not_found")
_NOT_INITIALIZED = fixed("lsp", "server_not_initialized")
_REQUEST_FAILED = fixed("lsp", "request_failed")
_HEADER = fixed("lsp", "header")
_SYNC_FULL = fixed("lsp", "sync_full")
_SYMBOL_KIND = fixed("lsp", "symbol_kind")
_WARNING = fixed("lsp", "severity_warning")
_INFORMATION = fixed("lsp", "severity_information")
_SOURCE = fixed("lsp", "source")
_UNIT = fixed("lsp", "position_unit")
_UNIT_BYTES = fixed("lsp", "unit_bytes")

_M_INITIALIZE = fixed("lsp", "initialize")
_M_SHUTDOWN = fixed("lsp", "shutdown")
_M_EXIT = fixed("lsp", "exit")
_M_DID_OPEN = fixed("lsp", "did_open")
_M_DID_CHANGE = fixed("lsp", "did_change")
_M_DID_SAVE = fixed("lsp", "did_save")
_M_DID_CLOSE = fixed("lsp", "did_close")
_M_SYMBOL = fixed("lsp", "workspace_symbol")
_M_HOVER = fixed("lsp", "hover")
_M_REFERENCES = fixed("lsp", "references")
_M_DIAGNOSTICS = fixed("lsp", "publish_diagnostics")

#: An inline link's target — `[text](target "title")` — and a reference
#: definition's — `[label]: target`. Both are what `fux ingest` records as a
#: `ref` edge; matching the live buffer rather than the committed edges is what
#: lets a diagnostic follow an unsaved edit.
_INLINE = re.compile(r"\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_DEFINITION = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*<?([^\s>]+)>?")
_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")


# -- the base protocol: Content-Length framing ---------------------------------


def read_message(stream) -> dict | None:
    """One framed message off a binary stream, or `None` at EOF.

    Headers end at a blank line; only `Content-Length` is read, because the one
    other header the spec names (`Content-Type`) has a single legal value.
    """
    length = None
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        name, _, value = line.decode("ascii", errors="replace").partition(":")
        if name.strip().lower() == _HEADER.lower():
            length = int(value.strip())
    if length is None:
        raise ValueError(f"a message with no {_HEADER} header")
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def write_message(stream, message: dict) -> None:
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")
    stream.write(f"{_HEADER}: {len(body)}\r\n\r\n".encode("ascii") + body)
    stream.flush()


# -- positions, URIs and links -------------------------------------------------


def _units(text: str) -> int:
    """`text`'s length in UTF-16 code units — an LSP column."""
    return len(text.encode("utf-16-le")) // _UNIT_BYTES


def _index(line: str, character: int) -> int:
    """The Python index on `line` of LSP column `character`."""
    seen = 0
    for i, ch in enumerate(line):
        if seen >= character:
            return i
        seen += _units(ch)
    return len(line)


def _range(line: int, start: int, end: int) -> dict:
    return {"start": {"line": line, "character": start}, "end": {"line": line, "character": end}}


def rel_of(root: Path, uri: str) -> str | None:
    """A `file://` URI as a repo-relative POSIX path, or `None` outside the repo."""
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    path = Path(url2pathname(parsed.path))
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def uri_of(root: Path, rel: str) -> str:
    return (root / rel).as_uri()


def target_id(source_rel: str, target: str) -> str | None:
    """The index id a link in `source_rel` points at, or `None` for no document.

    `#anchor` and `?query` are dropped; a pure anchor is a link into the same
    document and names no other. A leading `/` is the repository root. A path
    that climbs out of the repository names nothing fux could hold.
    """
    if target.startswith(("http://", "https://")):
        return "url:" + target
    if _SCHEME.match(target):
        return None
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return None
    if path.startswith("/"):
        joined = path.lstrip("/")
    else:
        joined = posixpath.join(posixpath.dirname(source_rel), path)
    norm = posixpath.normpath(joined)
    if norm.startswith("..") or norm == ".":
        return None
    return "file:" + norm


def links(text: str) -> list[tuple[int, int, int, str]]:
    """Every link in `text` as `(line, start, end, target)`, columns in UTF-16."""
    out = []
    for number, line in enumerate(text.splitlines()):
        for pattern in (_INLINE, _DEFINITION):
            for match in pattern.finditer(line):
                out.append((number, _units(line[: match.start()]), _units(line[: match.end()]), match.group(1)))
    return sorted(out)


# -- the server ----------------------------------------------------------------


class Server:
    """One connection's state: the open buffers and the resident index.

    `holder` is a `store.resident.Holder`, or `None` to read from disk on every
    request — which is what the unit tests do and what changes no answer.
    """

    def __init__(self, root: Path, *, top: int, holder=None) -> None:
        self.root = root
        self.top = top
        self.holder = holder
        self.documents: dict[str, str] = {}
        self.initialized = False
        self.shut_down = False
        self.outbox: list[dict] = []

    # -- the index -----------------------------------------------------------

    def _records(self) -> dict:
        from .store import read_index

        return read_index(self.root)

    def _text(self, rel: str) -> str:
        uri = uri_of(self.root, rel)
        if uri in self.documents:
            return self.documents[uri]
        path = self.root / rel
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _successor(records: dict, doc_id: str) -> str | None:
        for record in records.values():
            for edge in record.get("edges", ()):
                if edge.get("kind") == "supersedes" and edge.get("dst") == doc_id:
                    return record.get("loc")
        return None

    # -- features ------------------------------------------------------------

    def symbols(self, params: dict) -> list[dict]:
        from .query import run_query
        from .query.headings import headings_for

        query = str(params.get("query") or "").strip()
        if not query:
            return []
        results, _path = run_query(self.root, query, self.top, force_scan=False, use_tune=True)
        records = self._records() if results else {}
        out = []
        for r in results:
            if not r.id.startswith("file:"):
                continue
            heads = headings_for(records.get(r.id), query, limit=1)
            line = self._heading_line(r.loc, heads[0]) if heads else 0
            out.append({
                "name": r.title or r.loc,
                "kind": _SYMBOL_KIND,
                "location": {"uri": uri_of(self.root, r.loc), "range": _range(line, 0, 0)},
                "containerName": r.loc,
            })
        return out

    def _heading_line(self, rel: str, heading: str) -> int:
        for number, line in enumerate(self._text(rel).splitlines()):
            match = _HEADING.match(line)
            if match and heading in match.group(1):
                return number
        return 0

    def hover(self, params: dict) -> dict | None:
        uri = params["textDocument"]["uri"]
        rel = rel_of(self.root, uri)
        if rel is None:
            return None
        line_no = params["position"]["line"]
        character = params["position"]["character"]
        for number, start, end, target in links(self._buffer(uri, rel)):
            if number == line_no and start <= character <= end:
                doc_id = target_id(rel, target)
                records = self._records()
                record = records.get(doc_id) if doc_id else None
                if record is None:
                    return None
                return {
                    "contents": {"kind": "markdown", "value": self._card(records, doc_id, record)},
                    "range": _range(number, start, end),
                }
        return None

    def _card(self, records: dict, doc_id: str, record: dict) -> str:
        from .graph.model import Graph, edges_from_records

        graph = Graph(edges_from_records(list(records.values())))
        inbound = sum(1 for e in graph.edges if e.dst == doc_id and e.src in records)
        outbound = len(record.get("edges", ()))
        lines = [f"**{record.get('title') or record['loc']}**", "", f"`{record['loc']}`"]
        flags = []
        if record.get("archived"):
            flags.append("archived")
        if record.get("superseded"):
            successor = self._successor(records, doc_id)
            flags.append(f"superseded by `{successor}`" if successor else "superseded")
        if flags:
            lines += ["", " · ".join(flags)]
        facts = []
        if record.get("mtime") is not None:
            day = datetime.fromtimestamp(record["mtime"], tz=timezone.utc).date().isoformat()
            facts.append(f"committed {day}")
        facts.append(f"{inbound} linking here")
        facts.append(f"{outbound} links out")
        lines += ["", " · ".join(facts)]
        return "\n".join(lines)

    def references(self, params: dict) -> list[dict]:
        uri = params["textDocument"]["uri"]
        rel = rel_of(self.root, uri)
        if rel is None:
            return []
        doc_id = "file:" + rel
        records = self._records()
        sources = sorted({
            record["loc"]
            for record in records.values()
            for edge in record.get("edges", ())
            if edge.get("dst") == doc_id and record.get("id", "").startswith("file:")
        })
        out = []
        for source in sources:
            spots = [
                (number, start, end)
                for number, start, end, target in links(self._text(source))
                if target_id(source, target) == doc_id
            ] or [(0, 0, 0)]
            for number, start, end in spots:
                out.append({"uri": uri_of(self.root, source), "range": _range(number, start, end)})
        return out

    def diagnostics(self, uri: str) -> list[dict]:
        rel = rel_of(self.root, uri)
        if rel is None:
            return []
        records = self._records()
        out = []
        own = records.get("file:" + rel)
        if own is not None and (own.get("archived") or own.get("superseded")):
            state = "superseded" if own.get("superseded") else "archived"
            out.append({
                "range": _range(0, 0, 0),
                "severity": _INFORMATION,
                "source": _SOURCE,
                "message": f"this document is {state} in the fux index",
            })
        for number, start, end, target in links(self._buffer(uri, rel)):
            doc_id = target_id(rel, target)
            record = records.get(doc_id) if doc_id else None
            if record is None:
                continue
            if record.get("superseded"):
                successor = self._successor(records, doc_id)
                tail = f" — superseded by {successor}" if successor else ""
                message = f"links to a superseded document: {record['loc']}{tail}"
            elif record.get("archived"):
                message = f"links to an archived document: {record['loc']}"
            else:
                continue
            out.append({"range": _range(number, start, end), "severity": _WARNING, "source": _SOURCE, "message": message})
        return out

    def _buffer(self, uri: str, rel: str) -> str:
        return self.documents.get(uri) if uri in self.documents else self._text(rel)

    def _publish(self, uri: str) -> None:
        self.outbox.append({
            "jsonrpc": _JSONRPC,
            "method": _M_DIAGNOSTICS,
            "params": {"uri": uri, "diagnostics": self._call(self.diagnostics, uri)},
        })

    def _call(self, fn, *args):
        if self.holder is None:
            return fn(*args)
        with self.holder.call():
            return fn(*args)

    # -- dispatch ------------------------------------------------------------

    def handle(self, message: dict) -> dict | None:
        """One message in, the response out (`None` for a notification).

        Notifications this server publishes in reply — diagnostics — are queued
        on `outbox` and written by the loop after the response.
        """
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params") or {}
        if msg_id is None:
            self._notify(method, params)
            return None
        if method == _M_INITIALIZE:
            from . import __version__

            self.initialized = True
            return _ok(msg_id, {
                "capabilities": {
                    "positionEncoding": _UNIT,
                    "textDocumentSync": {"openClose": True, "change": _SYNC_FULL, "save": {"includeText": False}},
                    "hoverProvider": True,
                    "referencesProvider": True,
                    "workspaceSymbolProvider": True,
                },
                "serverInfo": {"name": _SOURCE, "version": __version__},
            })
        if not self.initialized:
            return _err(msg_id, _NOT_INITIALIZED, "initialize has not been received")
        if method == _M_SHUTDOWN:
            self.shut_down = True
            return _ok(msg_id, None)
        handlers = {_M_SYMBOL: self.symbols, _M_HOVER: self.hover, _M_REFERENCES: self.references}
        handler = handlers.get(method)
        if handler is None:
            return _err(msg_id, _METHOD_NOT_FOUND, f"unknown method {method!r}")
        try:
            return _ok(msg_id, self._call(handler, params))
        except FuxError as exc:
            return _err(msg_id, _REQUEST_FAILED, str(exc))

    def _notify(self, method, params: dict) -> None:
        document = params.get("textDocument") or {}
        uri = document.get("uri")
        if method == _M_DID_OPEN:
            self.documents[uri] = document.get("text", "")
            self._publish(uri)
        elif method == _M_DID_CHANGE:
            changes = params.get("contentChanges") or []
            if changes:
                self.documents[uri] = changes[-1].get("text", "")
            self._publish(uri)
        elif method == _M_DID_SAVE:
            self._publish(uri)
        elif method == _M_DID_CLOSE:
            self.documents.pop(uri, None)
            self.outbox.append({"jsonrpc": _JSONRPC, "method": _M_DIAGNOSTICS, "params": {"uri": uri, "diagnostics": []}})


def _ok(msg_id, result) -> dict:
    return {"jsonrpc": _JSONRPC, "id": msg_id, "result": result}


def _err(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": _JSONRPC, "id": msg_id, "error": {"code": code, "message": message}}


def serve(stdin=None, stdout=None, root: Path | None = None, *, enabled: bool) -> int:
    """Read framed messages until `exit` or EOF; the exit code is the spec's.

    `0` after `shutdown` then `exit`, `1` for an `exit` (or EOF) without one —
    LSP 3.17 §exit. `stdin`/`stdout` are binary streams, injectable so the
    protocol is tested without a subprocess, as `mcp.serve` is.

    How many symbols a search returns is the `top` `fux ask` shows a person —
    `[cli.ask]`/`[cli]` in `.fux/output.toml`, resolved once here. This is a
    surface for a person in an editor, not an agent, so it reads the person's
    number and not `[mcp]`'s. `enabled=False` is `--no-output-config`.
    """
    from .config import find_root
    from .output_config import load as load_output
    from .store.resident import Holder

    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    root = root or find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run `fux lsp` from inside a configured repo")
    top = int(load_output(root, enabled=enabled).resolve("ask", "top", as_json=False))
    server = Server(root, top=top, holder=Holder(root))
    while True:
        try:
            message = read_message(stdin)
        except ValueError:
            write_message(stdout, _err(None, _PARSE_ERROR, "parse error"))
            continue
        if message is None:
            return 0 if server.shut_down else 1
        if message.get("method") == _M_EXIT:
            return 0 if server.shut_down else 1
        response = server.handle(message)
        if response is not None:
            write_message(stdout, response)
        while server.outbox:
            write_message(stdout, server.outbox.pop(0))


def cmd_lsp(args) -> int:
    return serve(enabled=not getattr(args, "no_output_config", False))
