"""`fux mcp` — the stdio MCP server. W-76 Phase 5.

**Why this exists at all.** The consumer is an agent in a coding session, and
an agent calls a retrieval tool many times per task. A CLI spawn costs
~50-150 ms of Python start-up *before any ranking happens*, which is more than
the ranking itself (warm p95: 27 ms measured at 8 870 documents, 64 ms at
10 000). A warm process pays that once. The index, the doc table and the
postings mmaps stay resident across calls.

**Stdlib only.** No `mcp` package, no `pydantic`, no framework. MCP over stdio
is newline-delimited JSON-RPC 2.0, which is `json` and `sys.stdin` — adopting
a dependency to read a line and dump a dict would break L1 for convenience.

**The tool surface is deliberately smaller than the CLI.** `fux answer` is not
exposed: the agent *is* the answerer, and handing it a pre-composed answer
throws away the reason it called a retrieval tool. `explain`/`path` are folded
into `fux_related`, because an agent asking "what else was decided with this?"
does not care which of the three verbs it came from.

Every returned citation is `path:L12-L40` plus a `sha`, so the agent can open
exactly the cited span and verify it is the span that was ranked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .errors import FuxError

PROTOCOL_VERSION = "2024-11-05"

def _k_property() -> dict:
    """`k`'s advertised default, READ FROM THE ENGINE rather than retyped.

    ⚠ **This was a hand-written `5` and `[mcp] top` made it a lie.** Nothing
    failed: an MCP tool schema is a machine-facing declaration that no gate
    read, which is W-84's finding in the one surface where the reader is
    always a machine. The number now comes from `output_config.BUILT_IN`, and
    the description says the repo can change it — because it can.
    """
    from .output_config import BUILT_IN, OUTPUT_NAME

    return {
        "type": "integer",
        "description": (
            f"Maximum results (default {BUILT_IN['top']}; this repository's "
            f"{OUTPUT_NAME} may set a different default under [mcp])."
        ),
        "default": BUILT_IN["top"],
    }


TOOLS = [
    {
        "name": "fux_search",
        # ⚠ **This said "line-range citations" until 2026-08-26 and that was
        # false** -- `_search` returns a document path, a sha, and now the
        # matching headings; it has never returned a line range and by design
        # never will (see `_search`'s closing comment). An agent reading the
        # old text would look for a field that is not there, or believe fux
        # cannot do spans at all when `fux_passage` is the tool that does.
        # This is the same defect commit ad95a24 fixed in the human docs,
        # still live in the surface an agent actually reads. W-84.
        "description": (
            "Search the committed index for documents relevant to a natural-language "
            "question. Returns ranked documents with content hashes and the headings "
            "that match your query -- section-level, not line-level; call fux_passage "
            "for the lines. This is the call to make first for any 'where is X' or "
            "'why did we decide Y' question about this repository. "
            "READ THE `confidence` BLOCK BEFORE USING THE RESULTS. If "
            "`confidence.answerable` is false, do not answer from these results at "
            "all -- say what was searched and stop. If `confidence.band` is "
            "'partial', answer but name every term in `confidence.missing`: those "
            "are words from the question that appear in no document here. If it is "
            "'weak', the ranking could not separate the top hits, so report the "
            "candidates rather than a conclusion."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A natural-language question."},
                "k": _k_property(),
            },
            "required": ["query"],
        },
    },
    {
        "name": "fux_passage",
        "description": (
            "Read the verbatim text of a cited span, addressed as returned by "
            "fux_search. Use this instead of reading a whole file when you already "
            "have a citation: it returns only the cited lines and the hash they were "
            "read at."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "line_start": {"type": "integer"},
                "line_end": {"type": "integer"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "fux_related",
        "description": (
            "The neighbourhood around a document: what it links to, what links to it, "
            "what it supersedes or is superseded by, and whether it is archived. Use "
            "when a result raises 'what else was decided with this?'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


def _root() -> Path:
    from .config import find_root

    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run `fux mcp` from inside a configured repo")
    return root


def _search(root: Path, args: dict) -> dict:
    from .query import run_query
    from .query.headings import headings_for

    query = args.get("query") or ""
    # ADR-OUTPUT: `[mcp] top` is this surface's default, because a tool call
    # has no flags. An explicit `k` in the call still wins, exactly as a CLI
    # flag does. ⚠ There is deliberately no `[mcp] band`: the confidence block
    # below is UNCONDITIONAL here (ADR-CONFIDENCE decision 11).
    from .output_config import load as load_output

    k = int(args.get("k") or load_output(root).resolve("mcp", "top"))
    from .store import read_index

    signals: dict = {}
    results, path = run_query(root, query, k, force_scan=False, confidence_out=signals)
    block = signals.get("confidence")
    records = read_index(root) if results else {}
    out = []
    for r in results:
        record = records.get(r.id, {})
        out.append(
            {
                "path": r.loc,
                "title": r.title,
                "score": round(r.score, 6),
                # The hash the ranking was computed against. An agent that
                # reads the file and gets a different sha knows the index is
                # behind WITHOUT having to trust it -- which is the whole
                # premise of ranking from an index and fetching from the owner.
                "sha": record.get("sha", ""),
                "archived": r.archived,
                "superseded": bool(record.get("superseded", False)),
                # W-84 -- the document's headings that match this query, best
                # first, at most three. **Free here**: the record is already in
                # hand for `sha`, and `phrases` was committed at ingest. Always
                # present, `[]` when nothing matches or the record is `hashed`
                # (which carries no display text at all, L5) -- an absent key
                # would be indistinguishable from an older server.
                "headings": headings_for(record, query),
            }
        )
    return {
        "results": out,
        "ranked_by": path,
        # ADR-CONFIDENCE. **The single most important key on this surface**, and
        # the reason the record exists: an agent handed a ranked list cannot
        # tell "these documents answer your question" from "these are the
        # closest things in a corpus that never discusses it". Both look
        # identical -- a score, a title, a citation -- and the second is where
        # an agent invents an answer and cites a real file while doing it.
        #
        # `band` is what to branch on and `answerable: false` is a REFUSAL, not
        # a low score. `missing` names the query's own words the corpus does not
        # contain, which is what turns a vague hedge into "nothing here mentions
        # mTLS". `verified` is always `unverified` here: `fux_search` ranks from
        # the committed index and fetches nothing, and saying so is the point.
        "confidence": (block.as_dict() if block is not None else None),
        # **`fux_search` is document-level, deliberately.** Doc 06 of the ideal
        # set sketched line ranges on the search result itself, which would mean
        # fetching and chunking every hit on every search -- turning the cheap
        # call into the expensive one. The index knows documents; the refer
        # plane knows spans. `fux_passage` is one more call and it is the call
        # the agent was going to make anyway.
        #
        # **`headings` is not a retreat from that** (W-84). It is not a span and
        # does not pretend to be: no fetch, no chunking, no line arithmetic --
        # just the committed heading text, filtered to what the query asked
        # about. It narrows WHICH document to open and WHERE to look in it,
        # which is the decision an agent makes before it spends a `fux_passage`.
        "next": "call fux_passage with a path to read a span, or fux_related for neighbours",
    }


def _passage(root: Path, args: dict) -> dict:
    from .store import content_sha

    rel = args.get("path") or ""
    # Refuse to escape the repo. `resolve()` collapses `..` BEFORE the check,
    # so a traversal cannot slip through by being spelled differently.
    target = (root / rel).resolve()
    if not target.is_relative_to(root.resolve()):
        raise FuxError(f"{rel!r} resolves outside the repository")
    if not target.is_file():
        raise FuxError(f"{rel!r} is not a file in this repository")

    raw = target.read_bytes()
    lines = raw.decode("utf-8", errors="replace").splitlines()
    start = max(1, int(args.get("line_start") or 1))
    end = min(len(lines), int(args.get("line_end") or len(lines)))
    return {
        "path": rel,
        "line_start": start,
        "line_end": end,
        "sha": content_sha(raw),
        "text": "\n".join(lines[start - 1 : end]),
    }


def _related(root: Path, args: dict) -> dict:
    from .store import read_index

    rel = args.get("path") or ""
    doc_id = rel if rel.startswith(("file:", "url:")) else f"file:{rel}"
    records = read_index(root)
    record = records.get(doc_id)
    if record is None:
        raise FuxError(f"{rel!r} is not in the index")

    inbound = [
        {"path": other["loc"], "kind": edge["kind"]}
        for other in records.values()
        for edge in other.get("edges", ())
        if edge.get("dst") == doc_id
    ]
    return {
        "path": record["loc"],
        "title": record.get("title", ""),
        "archived": bool(record.get("archived", False)),
        "superseded": bool(record.get("superseded", False)),
        "outbound": [
            {"path": e["dst"].removeprefix("file:"), "kind": e["kind"]}
            for e in record.get("edges", ())
        ],
        "inbound": sorted(inbound, key=lambda e: (e["kind"], e["path"])),
    }


_HANDLERS = {"fux_search": _search, "fux_passage": _passage, "fux_related": _related}


def _handle(root: Path, message: dict) -> dict | None:
    """One JSON-RPC message in, one response out (or `None` for a notification)."""
    method = message.get("method")
    msg_id = message.get("id")

    # A notification has no id and MUST NOT be answered. `notifications/initialized`
    # arrives on every connection, and replying to it is a protocol error that
    # some hosts treat as fatal.
    if msg_id is None:
        return None

    if method == "initialize":
        from . import __version__

        return _ok(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fux", "version": __version__},
        })
    if method == "tools/list":
        return _ok(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        handler = _HANDLERS.get(name)
        if handler is None:
            return _err(msg_id, -32602, f"unknown tool {name!r}")
        try:
            payload = handler(root, params.get("arguments") or {})
        except FuxError as exc:
            # A tool-level failure is reported INSIDE the result with
            # `isError`, not as a JSON-RPC error: the agent should see it as a
            # tool that answered "no", which it can act on, rather than as a
            # transport fault, which it usually cannot.
            return _ok(msg_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        return _ok(msg_id, {
            "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
            "structuredContent": payload,
        })
    return _err(msg_id, -32601, f"unknown method {method!r}")


def _ok(msg_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _err(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def serve(stdin=None, stdout=None, root: Path | None = None) -> int:
    """Read newline-delimited JSON-RPC from stdin until EOF.

    `stdin`/`stdout` are injectable so the loop is testable without a
    subprocess — the protocol is the thing worth testing, and a pipe adds
    nothing but flakiness.
    """
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    root = root or _root()

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            stdout.write(json.dumps(_err(None, -32700, "parse error")) + "\n")
            stdout.flush()
            continue
        response = _handle(root, message)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
    return 0


def cmd_mcp(args) -> int:
    return serve()
